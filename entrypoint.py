import sys
import os
import subprocess
import time

import inotify.adapters
import inotify.constants as constants

class File:
    def __init__(self, path, is_dir):
        self.path = path
        self.is_dir = is_dir
        self.name = os.path.basename(path)
        self.parent = os.path.dirname(path) 

class Backlog:
    def __init__(self, zip_path):
        self.delete_backlog = {}
        self.update_backlog = {}
        self.zip_path = zip_path

        # Dictionary of paths to list of files
        self.dir_table = {
            '.' : {}
        }

    def __delete_table_recurse(self, path):
        if not path in self.dir_table:
            return {}
        children = self.dir_table.pop(path).values()
        for child in children:
            if child.is_dir:
                children += self.__delete_table_recurse(child.path)
        return children

    def process(self):
        for path in self.update_backlog:
            self.update_zip(path) 

        for path in self.delete_backlog:
            self.delete_zip(path, self.delete_backlog[path].is_dir) 

        self.update_backlog.clear()
        self.delete_backlog.clear()

    def add_update(self, path, is_dir):
        self.update_backlog[path] = File(path, is_dir) 

        f = File(path, is_dir)
        if is_dir:
            # Check if already exists in case a child event was received before
            # current directory was added e.g. /1/2/3 added before /1/2
            if not path in self.dir_table:
                self.dir_table[path] = {}
        else:   
            if not f.parent in self.dir_table:
                self.dir_table[f.parent] = {}
        self.dir_table[f.parent][f.name] = f

        # If most recent operation was updating a file, don't bother deleting
        if path in self.delete_backlog:
            self.delete_backlog.pop(path)

    def add_delete(self, path, is_dir):
        f = File(path, is_dir) 
        self.delete_backlog[f.path] = f 
        
        # Add child files to delete back log
        if is_dir:
            print "Marking %s for deletion" % self.dir_table[path]
            children = self.__delete_table_recurse(path)
            for child in children:
                self.delete_backlog[child.path] = child
        else:
            # If there are multiple files in directory, parent may be deleted already
            if f.parent in self.dir_table:
                if f.name in self.dir_table[f.parent]:
                    self.dir_table[f.parent].pop(f.name)

        # If most recent operation was deleting a file, don't bother updating
        if path in self.update_backlog:
            self.update_backlog.pop(path)

    def sync_zip(self):
        update_args = ['zip', '--symlink', 'FSr', self.zip_path, '.']
        print update_args
        process = subprocess.Popen(update_args)

    def update_zip(self, path):
        update_args = ['zip', '--symlink', '-r', self.zip_path, path]
        #print update_args
        child = subprocess.Popen(update_args)
        child.communicate()[0]
        returncode = child.returncode
        if returncode != 0 and returncode != 12:
            print returncode
            sys.exit()

    def delete_zip(self, path, is_dir):
        path = path + '/' if is_dir else path
        delete_args = ['zip', '-d', self.zip_path, path]
        #print delete_args
        child = subprocess.Popen(delete_args)
        child.communicate()[0]
        returncode = child.returncode
        if returncode != 0 and returncode != 12:
            print returncode
            sys.exit()

def parse_events(type_names):
    event = type_names[0]
    is_dir = False
    if len(type_names) > 1:
        if type_names[1] == 'IN_ISDIR':
            is_dir = True
        elif event == 'IN_ISDIR':
            event = type_names[1]
            is_dir = True
    return event, is_dir

def _main():
    mask = (constants.IN_MODIFY | constants.IN_MOVE | constants.IN_CREATE | 
        constants.IN_DELETE | constants.IN_DELETE_SELF)
    i = inotify.adapters.InotifyTree('.', mask = mask)

    if len(sys.argv) != 2:
        print 'Expecting argument one to be an absolute path to the storage archive.'
        sys.exit(1)
    
    zip_path = sys.argv[1]
    if not os.path.exists(zip_path):
        print "Creating %s..." % sys.argv[1] 
        process = subprocess.Popen(['zip', zip_path, '.', '-i', '.'])
    
    backlog = Backlog(zip_path)
    checkpoint = time.time()
    for event in i.event_gen(yield_nones=False):
        timestamp = time.time()
        (_, type_names, dir_path, filename) = event
        path = os.path.join(dir_path, filename)
        print "{} -> {}".format(type_names, path)
        
        event, is_dir = parse_events(type_names)
        if event == 'IN_IGNORED':
            continue

        if event == 'IN_DELETE' or event == 'IN_DELETE_SELF' or event == 'IN_MOVED_FROM':
            backlog.add_delete(path, is_dir)
            
            #jif is_dir:
             #   recurse_add_delete(path, delete_backlog)

            #if is_dir and (event == 'IN_DELETE_SELF' or event == 'IN_MOVED_FROM'):
            #    i.inotify.remove_watch(path)
     	else:
            backlog.add_update(path, is_dir) 
            
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path, topdown=True):
                    for name in dirs:
                        path = os.path.join(root, name)
                        backlog.add_update(path, True)

                        # See race condition in docs to see why this is necessary
                        i.inotify.add_watch(path, mask)
                    for name in files:
                        path = os.path.join(root, name)
                        backlog.add_update(path, False)
        
        if timestamp - checkpoint > 5:
            print '\nProcessing backlog...'
            backlog.process()
            checkpoint = timestamp
            print ''

if __name__ == '__main__':
    _main()
