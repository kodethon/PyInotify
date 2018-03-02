test_dir=home
container_zip_path=/tmp/test.zip
host_zip_path=tmp/test.zip
test_container_name=test-inotify

mkdir $test_dir 
rm -rf $test_dir/*
sudo rm $host_zip_path

docker rm -f $test_container_name
docker run --name $test_container_name -d -v $(pwd)/$test_dir:/home/kodethon -v $(pwd)/tmp:/tmp jvlythical/fs:py $container_zip_path

sleep 5 # Wait for initialization
python test.py $test_dir $host_zip_path 10
