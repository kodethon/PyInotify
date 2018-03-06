test_dir=home
tmp_dir=tmp
container_zip_path=/tmp/test.zip
host_zip_path=tmp/test.zip
test_container_name=test-inotify

mkdir $tmp_dir 2> /dev/null
mkdir $test_dir 2> /dev/null
rm -rf $test_dir/*
sudo rm $host_zip_path

docker rm -f $test_container_name 2> /dev/null
docker run --name $test_container_name -itd \
-v $(pwd)/../..:/sbin/PyInotify \
-v $(pwd)/$test_dir:/home/kodethon -v $(pwd)/tmp:/tmp jvlythical/fs:py > /dev/null \
$container_zip_path

sleep 5 # Wait for initialization
echo 'Starting the test...'
python test.py $test_dir $host_zip_path 1000
docker logs test-inotify  --tail 100 > tmp/docker.log
