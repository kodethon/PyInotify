import sys
import os
import subprocess
import time
import logging

import inotify.adapters
import inotify.constants as constants

# Keeps track of what events need to be processed
class Backlog(object):
    
    class File:
        def __init__(self, path, is_dir):
            self.path = path
            self.is_dir = is_dir
            self.name = os.path.basename(path)
            self.parent = os.path.dirname(path) 

    def __init__(self):
        self.delete_backlog = {}
        self.update_backlog = {}
        self.event_count = 0

    def add_update(self, path, is_dir):
        self.update_backlog[path] = self.File(path, is_dir) 

        # If most recent operation was updating a file, don't bother deleting
        if path in self.delete_backlog:
            self.delete_backlog.pop(path)
        self.event_count += 1

    def add_delete(self, path, is_dir):
        f = self.File(path, is_dir) 
        self.delete_backlog[f.path] = f 

        # If most recent operation was deleting a file, don't bother updating
        if path in self.update_backlog:
            self.update_backlog.pop(path)
        self.event_count += 1

    def process(self):
        pass 
    
    def sync(self):
        pass

    def update(self, path, is_dir):
        pass

    def delete(self, path, is_dir):
        pass

class ZipBacklog(Backlog):
    def __init__(self, archive_path, process_interval = 5):
        super(ZipBacklog, self).__init__()

        self.archive_path = archive_path
        self.process_interval = process_interval

        if not os.path.exists(archive_path):
            print "Creating %s..." % archive_path
            process = subprocess.Popen(['zip', archive_path, '.', '-i', '.'])

        self.sync() # Sync directory with zip

    def create_dirty_flag(self):
        # Create file denoting changes have been made
        archive_dir = os.path.dirname(self.archive_path)
        dirty_flag = os.path.join(archive_dir, '__DIRTY__')
        if not os.path.exists(dirty_flag):
            open(dirty_flag, 'a').close()

    def process(self):
        for path in self.update_backlog:
            self.update(path, self.update_backlog[path].is_dir) 

        for path in self.delete_backlog:
            self.delete(path, self.delete_backlog[path].is_dir) 
        
        self.create_dirty_flag()
        self.update_backlog.clear()
        self.delete_backlog.clear()

    def sync(self):
        update_args = ['zip', '--symlink', '-FSr', self.archive_path, '.']
        process = subprocess.Popen(update_args)

    def update(self, path, is_dir):
        update_args = ['zip', '--symlink', '-ru', self.archive_path, path]
        child = subprocess.Popen(update_args)
        child.communicate()[0]
        returncode = child.returncode
        if returncode != 0 and returncode != 12:
            logging.error("Zip returned a non-success error code: %s" % returncode)
            sys.exit()

    def delete(self, path, is_dir):
        path = path + '/*' if is_dir else path
        delete_args = ['zip', '-d', self.archive_path, path]
        child = subprocess.Popen(delete_args)
        child.communicate()[0]
        returncode = child.returncode
        if returncode != 0 and returncode != 12:
            logging.error("Zip returned a non-success error code: %s" % returncode)
            sys.exit()

class LazyZipBacklog(ZipBacklog):
    def __init__(self, archive_path):
        super(LazyZipBacklog, self).__init__(archive_path, 1)
        self.last_process = time.time()

    def process(self):
        timestamp = time.time()

        time_threshold = timestamp - self.last_process > 60 and self.event_count > 5
        event_threshold = self.event_count > 30
        if not time_threshold and not event_threshold:
            logging.debug("Event count: %s" % self.event_count)
        else:
            logging.info("Syncing files to %s" % self.archive_path)

            self.sync()
            self.create_dirty_flag()
            
            self.event_count = 0
            self.last_process = timestamp

        self.update_backlog.clear()
        self.delete_backlog.clear()   

class PyInotifyFacade:
    
    @staticmethod
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
    if len(sys.argv) != 2:
        print 'Expecting argument one to be an absolute path to the storage archive.'
        sys.exit(1)

    mask = (constants.IN_MODIFY | constants.IN_MOVE | constants.IN_CREATE | 
        constants.IN_DELETE | constants.IN_DELETE_SELF)
    i = inotify.adapters.InotifyTree('.', mask = mask)

    archive_path = sys.argv[1]
    backlog = LazyZipBacklog(archive_path) 

    # Iterate through events as they are received
    checkpoint = time.time() # Last time zip was updated
    for event in i.event_gen(yield_nones=False):
        timestamp = time.time()
        (_, type_names, dir_path, filename) = event
        path = os.path.join(dir_path, filename)
        logging.debug("{} -> {}".format(type_names, path))
        
        event, is_dir = PyInotifyFacade.parse_events(type_names)
        if event == 'IN_IGNORED':
            continue

        if event == 'IN_DELETE' or event == 'IN_DELETE_SELF' or event == 'IN_MOVED_FROM':
            # Handle delete
            backlog.add_delete(path, is_dir)
     	else:
     	    # Handle updates
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
        
        if timestamp - checkpoint > backlog.process_interval:
            logging.debug('Processing backlog...')
            backlog.process()
            checkpoint = timestamp

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,  format="%(levelname)s - %(message)s")
    _main()
