FROM ubuntu:18.04

RUN apt-get update && apt-get install -y python git zip && rm -rf /var/lib/apt/lists/*

RUN userdel www-data && groupadd -g 33 kodethon && \
	useradd -d /home/kodethon -m -s /bin/bash -u 33 -g kodethon kodethon && \ 
	usermod -aG sudo kodethon; echo 'kodethon ALL=(ALL) NOPASSWD: ALL' >> /etc/sudoers

# Set home directory
WORKDIR /home/kodethon

ENTRYPOINT ["python", "/sbin/PyInotify/entrypoint.py"] 

RUN cd /sbin && git clone https://github.com/kodethon/PyInotify.git
