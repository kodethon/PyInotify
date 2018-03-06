cd tmp

zip_file=test.zip
dest=sandbox

rm -rf $dest
mkdir $dest
cp $zip_file $dest
cd $dest && unzip $zip_file; rm $zip_file
