import sys
import os
import zipfile
import time
import string

from random import *

def check_file_created(container_file_path, zip_path, iteration = 0):
    ''' Check file exists in zip file '''
    time.sleep(iteration + 1)
    zf = zipfile.ZipFile(zip_path, 'r')
    paths_in_zip = zf.namelist()
    try:
        found = paths_in_zip.index(container_file_path)
        print "Test succeeded after iteration %s" % iteration
    except ValueError:
        check_file_created(container_file_path, zip_path, iteration + 1)

def check_file_updated(container_file_path, text, zip_path, iteration = 0):
    ''' Check file in zip exists and its contents match text '''
    time.sleep(iteration + 1)
    zf = zipfile.ZipFile(zip_path, 'r')
    try:
        data = zf.read(container_file_path)
    except KeyError:
        return check_file_updated(container_file_path, text, zip_path, iteration + 1)

    if data == text:
        print "Test succeeded after iteration %s" % iteration
    else:
        print "Zip data has length: %s while expected length is: %s" % (len(data), len(text))
        sys.exit()

def main():
    if len(sys.argv) < 4:
        print "USAGE: python test.py <TEST_DIR> <ZIP_PATH> <ITERATIONS>" 
        sys.exit(1)

    test_dir=sys.argv[1]
    zip_path=sys.argv[2]
    iterations=int(sys.argv[3])

    char_set = string.ascii_lowercase + string.digits + '_-'
    dir_list = [test_dir]
    for i in xrange(0, iterations):
        print('')

        # Create a random file path based on current structure
        path = dir_list[randint(0, len(dir_list) - 1)]
        filename = []
        for _ in range(randint(1, 50)):
            filename += char_set[randint(0, len(char_set) - 1)] 
        path = os.path.join(path, ''.join(filename))

        # Create the file or directory
        is_dir = randint(0, 1) == 0
        text = ''
        if is_dir:
            path += '/'
            print 'Creating folder: %s' % path
            os.mkdir(path)
            dir_list.append(path)
        else:
            print 'Creating file: %s' % path
            fp = open(path, 'a')
            
            num_chars = randint(0, 1000)
            batch_size = randint(1, 100)
            print 'Writing %s characters with a batch size of %s' % (num_chars, batch_size)
            batch = ''
            for i in xrange(0, num_chars):
                char = char_set[randint(0, len(char_set) - 1)] 
                batch += char
                if i % batch_size == 0 or i == num_chars - 1:
                    fp.write(batch) 
                    batch = ''
                text += char
            fp.close()
        
        # Check if test succeeded
        container_path = path.replace(test_dir + '/', '', 1)
        if is_dir:
            check_file_created(container_path, zip_path) 
        else:
            check_file_updated(container_path, text, zip_path)

if __name__ == '__main__':
    main()
