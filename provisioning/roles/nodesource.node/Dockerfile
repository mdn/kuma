FROM ubuntu:trusty
MAINTAINER Mark Wolfe <mark@wolfe.id.au>

# http://docs.ansible.com/ansible/intro_installation.html#latest-releases-via-apt-ubuntu
RUN apt-get install software-properties-common -y --force-yes
RUN apt-add-repository ppa:ansible/ansible
RUN apt-get update
RUN apt-get install ansible -y --force-yes


ENV WORKDIR /build/ansible-nodejs
ADD . /build/ansible-nodejs
ADD . /etc/ansible/roles/ansible-nodejs-role
ADD ./tests/localhosts /etc/ansible/hosts

RUN ansible-playbook $WORKDIR/role.yml -c local
RUN node -v
