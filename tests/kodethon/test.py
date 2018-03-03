import sys
import os
import zipfile
import time
import string
import shutil

from random import *

class Tester:
    
    def __init__(self, test_dir, zip_path):
        self.test_dir = test_dir
        self.zip_path = zip_path
        self.update_table = {}
        self.delete_table = {}
        self.dir_list = [test_dir]
        self.file_list = []
        self.total_tests = 0
        self.passed_tests = 0

    def is_finished(self):
        return self.passed_tests == self.total_tests

    def to_container_path(self, path):
        return path.replace(self.test_dir + '/', '', 1)

    def apply_check(self):
        updated_paths = []
        for path in self.update_table:
            updated_path = self.check_file_created(path, self.update_table[path]['is_dir'])
            if updated_path:
                updated_paths.append(updated_path)
        
        for path in updated_paths:
            self.update_table.pop(path)
        
        self.passed_tests += len(updated_paths)

        deleted_paths = []
        for path in self.delete_table:
            deleted_path = self.check_file_deleted(path, self.delete_table[path]['is_dir'])
            if deleted_path:
                deleted_paths.append(deleted_path)
        
        for path in deleted_paths:
            self.delete_table.pop(path)

        self.passed_tests += len(deleted_paths)
        print "Passed: %s - Pending: %s" % (self.passed_tests, self.total_tests - self.passed_tests)

    def check_file_created(self, path, is_dir):
        ''' Check file exists in zip file '''
        container_file_path = self.to_container_path(path)
        zf = zipfile.ZipFile(self.zip_path, 'r')
        paths_in_zip = zf.namelist()
        try:
            found = paths_in_zip.index(container_file_path if not is_dir else container_file_path + '/')
            print "%s exists after %s event(s)." % (path, self.update_table[path]['timestamp']) 
            return path
        except ValueError:
            self.update_table[path]['timestamp'] += 1
            print "%s is missing for %s event(s)." % (path, self.update_table[path]['timestamp']) 

    def check_file_deleted(self, path, is_dir):
        ''' Check file does not exist in zip file '''
        container_file_path = self.to_container_path(path)
        zf = zipfile.ZipFile(self.zip_path, 'r')
        paths_in_zip = zf.namelist()
        try:
            found = paths_in_zip.index(container_file_path if not is_dir else container_file_path + '/')
            self.delete_table[path]['timestamp'] += 1
            print "%s has existed for %s event(s)." % (path, self.delete_table[path]['timestamp']) 
        except ValueError:
            print "%s has been deleted after %s event(s)." % (path, self.delete_table[path]['timestamp'])
            return path

    def check_file_updated(self, path, text):
        ''' Check file in zip exists and its contents match text '''
        container_file_path = self.to_container_path(path)
        zf = zipfile.ZipFile(self.zip_path, 'r')
        try:
            data = zf.read(container_file_path)
            if data == text:
                print "%s contents updated after %s event(s)." % (path, self.update_table(path)['timestamp'])
                return path
            else:
                self.update_table[path]['timestamp'] += 1
                print "Zip data has length: %s while expected length is: %s" % (len(data), len(text))
        except KeyError:
            self.update_table[path]['timestamp'] += 1
            print "%s is missing for %s event(s)." % (path, self.update_table[path]['timestamp']) 

    def pick_random_file(self, file_list):
        if len(file_list) == 0:
            return None
        return file_list[randint(0, len(file_list) - 1)]

    def pop_random_file(self, file_list):
        index = randint(0, len(file_list) - 1)
        f = file_list[index]
        file_list.pop(index)
        return f
    
    def watch_update(self, path, is_dir):
        print "Watching %s for update..." % path
        self.update_table[path] = {
            'timestamp' : 0,
            'is_dir' : is_dir
        }
        self.total_tests += 1
        if path in self.delete_table:
            self.delete_table.pop(path)
            self.total_tests -= 1

    def watch_delete(self, path, is_dir):
        print "Watching %s for deletion..." % path
        self.delete_table[path] = {
            'timestamp' : 0,
            'is_dir' : is_dir
        }
        self.total_tests += 1
        if path in self.update_table:
            self.update_table.pop(path)
            self.total_tests -= 1

    def create_test_case(self):
        char_set = string.ascii_lowercase + string.digits + '_-'

        # Create a random dir path based on current structure
        path = self.pick_random_file(self.dir_list)
        filename = []
        for _ in range(randint(1, 50)):
            filename += char_set[randint(0, len(char_set) - 1)] 
        path = os.path.join(path, ''.join(filename))

        # Create the file or directory
        is_dir = randint(0, 1) == 0
        if is_dir:
            print 'Creating folder: %s' % path
            self.dir_list.append(path)
            os.mkdir(path)
        else:
            print 'Creating file: %s' % path
            fp = open(path, 'a')
            self.file_list.append(path)
        
        self.watch_update(path, is_dir) 

    def modify_test_case(self):
        char_set = string.ascii_lowercase + string.digits + '_-'

        # Create a random dir path based on current structure
        path = self.pick_random_file(self.dir_list)
        filename = []
        for _ in range(randint(1, 50)):
            filename += char_set[randint(0, len(char_set) - 1)] 
        path = os.path.join(path, ''.join(filename))

        # If use existing, pick an existing file
        use_existing = randint(0, 1) == 0
        if not use_existing:
            self.file_list.append(path)
        else:
            if len(self.file_list) == 0:
                print 'No files to modify, continuing...'
            else:
                path = self.pick_random_file(self.file_list)
                fp = open(path, 'rw+')
                fp.truncate(0)
                fp.close()

        print 'Modifying file: %s' % path

        fp = open(path, 'a')
        num_chars = randint(0, 1000)
        batch_size = randint(1, 100)
        print 'Writing %s characters with a batch size of %s' % (num_chars, batch_size) 

        text = ''
        batch = ''
        for i in xrange(0, num_chars):
            char = char_set[randint(0, len(char_set) - 1)] 
            batch += char
            if i % batch_size == 0 or i == num_chars - 1:
                fp.write(batch) 
                batch = ''
            text += char
        fp.close()
        self.watch_update(path, False)
        
    def delete_test_case(self):
        is_dir = randint(0, 1) == 0
        if is_dir:
            path = self.pop_random_file(self.dir_list)
            if path == self.test_dir:
                print 'Root folder selected, continuing...\n'
                self.dir_list.append(path)
            else:
                print 'Deleting folder: %s' % path
                marked_files = []
                marked_dirs = []
                for root, dirs, files in os.walk(path, topdown=False):
                    for name in files:
                        marked_files.append(os.path.join(root, name))
                    for name in dirs:
                        marked_dirs.append(os.path.join(root, name))
                shutil.rmtree(path)
                
                # Checked that children are also removed
                for path in marked_files:
                    self.watch_delete(path, False)
                    self.file_list.remove(path)

                for path in marked_dirs:
                    self.watch_delete(path, True)
                    self.dir_list.remove(path)

                self.watch_delete(path, is_dir)
        else:
            if len(self.file_list) == 0:
                print 'No files to delete, continuing...'
            else:
                path = self.pop_random_file(self.file_list)
                print 'Deleting file: %s' % path
                os.remove(path)
                self.watch_delete(path, is_dir)

def main():
    if len(sys.argv) < 4:
        print "USAGE: python test.py <TEST_DIR> <ZIP_PATH> <ITERATIONS>" 
        sys.exit(1)

    events = ['IN_MODIFY', 'IN_DELETE', 'IN_CREATE']

    test_dir = sys.argv[1]
    zip_path = sys.argv[2]
    iterations  = int(sys.argv[3])
    tester = Tester(test_dir, zip_path)

    for i in xrange(0, iterations):
        print ''

        # Pick an event and set it up
        event = events[randint(0, len(events) - 1)]
        if event == 'IN_CREATE':
            tester.create_test_case() 
        elif event == 'IN_DELETE':
            tester.delete_test_case()
        elif event == 'IN_MODIFY':       
            tester.modify_test_case()

        time.sleep(1)
        tester.apply_check()
    
    while not tester.is_finished():
        tester.apply_check()
        time.sleep(1)

if __name__ == '__main__':
    main()
