import sys
import os
import subprocess

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

    for event in i.event_gen(yield_nones=False):
        (_, type_names, dir_path, filename) = event
        path = os.path.join(dir_path, filename)
        print "\n{} -> {}".format(type_names, path)
        
        event = type_names[0]
        is_dir = len(type_names) > 1 and type_names[1] == 'IN_ISDIR'
        if event == 'IN_DELETE_SELF' or event == 'IN_DELETE' or event == 'IN_MOVED_FROM':
            delete_args = ['zip', '-d', zip_path, path + '/' if is_dir else path]
            print delete_args
            process = subprocess.Popen(delete_args)
            
            # Fix crashing issue...
            if event == 'IN_DELETE_SELF':
                i.inotify.remove_watch(path)
        else:
            update_args = ['zip', '--symlink', zip_path, path]
            print update_args
            process = subprocess.Popen(update_args)

if __name__ == '__main__':
    _main()
