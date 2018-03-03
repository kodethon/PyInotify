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
        self.update_list = []
        self.delete_list = []
        self.dir_list = [test_dir]
        self.file_list = []

    def to_container_path(self, path):
        return path.replace(self.test_dir + '/', '', 1)

    def check_file_created(self, path, is_dir, iteration = 0):
        ''' Check file exists in zip file '''
        container_file_path = self.to_container_path(path)
        time.sleep(iteration + 1)
        zf = zipfile.ZipFile(self.zip_path, 'r')
        paths_in_zip = zf.namelist()
        try:
            found = paths_in_zip.index(container_file_path if not is_dir else container_file_path + '/')
            print "Test succeeded after iteration %s" % iteration
        except ValueError:
            self.check_file_created(container_file_path, is_dir, iteration + 1)

    def check_file_deleted(self, path, is_dir, iteration = 0):
        ''' Check file does not exist in zip file '''
        container_file_path = self.to_container_path(path)
        time.sleep(iteration + 1)
        zf = zipfile.ZipFile(self.zip_path, 'r')
        paths_in_zip = zf.namelist()
        try:
            found = paths_in_zip.index(container_file_path if not is_dir else container_file_path + '/')
            self.check_file_deleted(container_file_path, is_dir, iteration + 1)
        except ValueError:
            print "Test succeeded after iteration %s" % iteration

    def check_file_updated(self, path, text, iteration = 0):
        ''' Check file in zip exists and its contents match text '''
        container_file_path = self.to_container_path(path)
        time.sleep(iteration + 1)
        zf = zipfile.ZipFile(self.zip_path, 'r')
        try:
            data = zf.read(container_file_path)
        except KeyError:
            return self.check_file_updated(container_file_path, text, iteration + 1)

        if data == text:
            print "Test succeeded after iteration %s" % iteration
        else:
            print "Zip data has length: %s while expected length is: %s" % (len(data), len(text))
            return self.check_file_updated(container_file_path, text, iteration + 1)

    def pick_random_file(self, file_list):
        if len(file_list) == 0:
            return None
        return file_list[randint(0, len(file_list) - 1)]

    def pop_random_file(self, file_list):
        index = randint(0, len(file_list) - 1)
        f = file_list[index]
        file_list.pop(index)
        return f

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

        self.check_file_created(path, is_dir) 

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

        self.check_file_updated(path, text)

    def delete_test_case(self):
        is_dir = randint(0, 1) == 0
        if is_dir:
            path = self.pop_random_file(self.dir_list)
            if path == self.test_dir:
                print 'Root folder selected, continuing...'
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
                self.check_file_deleted(path, is_dir)
                
                # Checked that children are also removed
                for path in marked_files:
                    print 'Checking if file %s is deleted...' % path
                    self.check_file_deleted(path, is_dir)
                    self.file_list.remove(path)
                for path in marked_dirs:
                    print 'Checking if folder %s is deleted...' % path
                    self.check_file_deleted(path, is_dir)
                    self.dir_list.remove(path)
        else:
            if len(self.file_list) == 0:
                print 'No files to delete, continuing...'
            else:
                path = self.pop_random_file()
                print 'Deleting file: %s' % path
                os.remove(path)
                self.check_file_deleted(path, is_dir)

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
        
if __name__ == '__main__':
    main()
