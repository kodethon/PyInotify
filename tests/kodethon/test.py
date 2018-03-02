import sys
import os
import uuid
import zipfile
import time

from random import *

if len(sys.argv) < 4:
    print "USAGE: python test.py <TEST_DIR> <ZIP_PATH> <ITERATIONS>" 
    sys.exit(1)
 
test_dir=sys.argv[1]
zip_path=sys.argv[2]
iterations=int(sys.argv[3])

dir_list = [test_dir]
for i in xrange(0, iterations):
    print('')

    # Create a random file path based on current structure
    path = dir_list[randint(0, len(dir_list) - 1)]
    filename = str(uuid.uuid4())[0:5]
    path = os.path.join(path, filename)

    # Create the file or directory
    is_dir = randint(0, 1) == 0
    if is_dir:
        path += '/'
        print 'Creating folder: %s' % path
        os.mkdir(path)
        dir_list.append(path)
    else:
        print 'Creating file: %s' % path
        open(path, 'a').close()
    
    time.sleep(1) # Add delay

    zf = zipfile.ZipFile(zip_path, 'r')
    paths_in_zip = zf.namelist()
    try:
        print paths_in_zip.index(path.replace(test_dir + '/', '', 1))
    except ValueError:
        print paths_in_zip
