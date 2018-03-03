import sys
import os
import subprocess
import time

import inotify.adapters

def _main():
    i = inotify.adapters.InotifyTree('.')
    #i.add_watch('.')

    if len(sys.argv) != 2:
        print 'Expecting argument one to be an absolute path to the storage archive.'
        sys.exit(1)
    
    zip_path = sys.argv[1]
    if not os.path.exists(zip_path):
        print "Creating %s..." % sys.argv[1] 
        process = subprocess.Popen(['zip', zip_path, '.', '-i', '.'])
    
    delete_backlog = {}
    update_backlog = {}
    checkpoint = time.time()
    for event in i.event_gen(yield_nones=False):
        timestamp = time.time()
        (_, type_names, dir_path, filename) = event
        path = os.path.join(dir_path, filename)
        print "{} -> {}".format(type_names, path)
        
        event = type_names[0]
        if event == 'IN_IGNORED':
            continue

        is_dir = False
        if event == 'IN_ISDIR':
            event = type_names[1]
            is_dir = True

        if event == 'IN_DELETE_SELF' or event == 'IN_DELETE' or event == 'IN_MOVED_FROM':
            # If delete operation
            delete_backlog[path] = {
                'is_dir' : is_dir
            }

            # If most recent operation was deleting a file, don't bother updating
            if path in update_backlog:
                update_backlog.pop(path)
            
            # Fix crashing issue...
            #if event == 'IN_DELETE_SELF':
            #    i.inotify.remove_watch(path)
        else:
            update_backlog[path] = {
                'is_dir' : is_dir
            }

            # If most recent operation was updating a file, don't bother deleting
            if path in delete_backlog:
                delete_backlog.pop(path)
        
        if timestamp - checkpoint > 5:
            print '\nProcessing backlog...'
            process_deferred_updates(update_backlog, delete_backlog, zip_path)
            checkpoint = timestamp
            print ''

def process_deferred_updates(update_backlog, delete_backlog, zip_path):
    for path in update_backlog:
        update_zip(path, zip_path) 

    for path in delete_backlog:
        delete_zip(path, delete_backlog[path]['is_dir'], zip_path) 

    update_backlog.clear()
    delete_backlog.clear()

def sync_zip(zip_path):
    update_args = ['zip', '--symlink', 'FSr', zip_path, '.']
    print update_args
    process = subprocess.Popen(update_args)

def update_zip(path, zip_path):
    update_args = ['zip', '--symlink', zip_path, path]
    print update_args
    child = subprocess.Popen(update_args)
    child.communicate()[0]
    returncode = child.returncode
    if returncode != 0 and returncode != 12:
        print returncode
        sys.exit()

def delete_zip(path, is_dir, zip_path):
    path = path + '/' if is_dir else path
    delete_args = ['zip', '-d', zip_path, path]
    print delete_args
    child = subprocess.Popen(delete_args)
    child.communicate()[0]
    returncode = child.returncode
    if returncode != 0 and returncode != 12:
        print returncode
        sys.exit()

if __name__ == '__main__':
    _main()
