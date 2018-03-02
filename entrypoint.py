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
    
    deferred_updates = {}
    for event in i.event_gen(yield_nones=False):
        (_, type_names, dir_path, filename) = event
        path = os.path.join(dir_path, filename)
        print "\n{} -> {}".format(type_names, path)
        
        event = type_names[0]
        if event == 'IN_IGNORED':
            continue
        
        is_dir = False
        if event == 'IN_ISDIR':
            event = type_names[1]
            is_dir = True

        if event == 'IN_DELETE_SELF' or event == 'IN_DELETE' or event == 'IN_MOVED_FROM':
            # If delete operation
            delete_args = ['zip', '-d', zip_path, path + '/' if is_dir else path]
            print delete_args
            process = subprocess.Popen(delete_args)
            
            # Fix crashing issue...
            if event == 'IN_DELETE_SELF':
                i.inotify.remove_watch(path)
        else:
            # If update operation
            if not is_dir:
                c = os.path.getsize(path)
                time.sleep(1)
                file_size = os.path.getsize(path)
                if file_size != c:
                    # Defer updates until the file has stopped changing size
                    deferred_updates[path] = file_size
                    continue
                else:
                    update_zip(path, zip_path)
            else:
                update_zip(path, zip_path)
        
        # Updates are grouped so that writes in quick succession don't spam zip calls
        process_deferred_updates(deferred_updates, zip_path)

def process_deferred_updates(deferred_updates, zip_path):
    processed_paths = []
    for path in deferred_updates:
        print 'Checking deferred update: %s' % path

        prev_file_size = deferred_updates[path]
        cur_file_size = os.path.getsize(path)
        if prev_file_size != cur_file_size:
            print "Previous size: %s - Current size: %s" % (prev_file_size, cur_file_size)
        else:
            update_zip(path, zip_path) 
            processed_paths.append(path)

    for path in processed_paths:
        deferred_updates.pop(path)

def update_zip(path, zip_path):
    update_args = ['zip', '--symlink', zip_path, path]
    print update_args
    process = subprocess.Popen(update_args)

if __name__ == '__main__':
    _main()
