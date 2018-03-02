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
    #timestamp = time.time()
    #backlog = 0
    for event in i.event_gen(yield_nones=False):
        '''
        t = time.time()

        if backlog > 0:
            if time.time() - timestamp > 5:
                print 'Syncing zip...'
                sync_zip(zip_path)
                backlog = 0
                timestamp = t
            continue 
        elif t - timestamp < 0.5:
            print 'Batching events...'
            backlog += 1
            timestamp = t
            continue
        '''

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
            delete_zip(path, is_dir, zip_path) 
            
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

def sync_zip(zip_path):
    update_args = ['zip', '--symlink', 'FSr', zip_path, '.']
    print update_args
    process = subprocess.Popen(update_args)

def update_zip(path, zip_path):
    update_args = ['zip', '--symlink', zip_path, path]
    print update_args
    process = subprocess.Popen(update_args)

def delete_zip(path, is_dir, zip_path):
    path = path + '/' if is_dir else path
    delete_args = ['zip', '-d', zip_path, path]
    print delete_args
    process = subprocess.Popen(delete_args)
    time.sleep(0.025)

if __name__ == '__main__':
    _main()
