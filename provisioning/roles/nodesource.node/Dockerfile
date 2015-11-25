FROM ubuntu:trusty
MAINTAINER Mark Wolfe <mark@wolfe.id.au>

RUN apt-get update
RUN apt-get install -y --force-yes \
	python-pycurl \
	python-apt \
	ansible \
	lsb-release

ENV WORKDIR /build/ansible-nodejs
ADD . /build/ansible-nodejs
ADD ./tests/localhosts /etc/ansible/hosts

RUN ansible-playbook $WORKDIR/role.yml -c local
RUN node -v