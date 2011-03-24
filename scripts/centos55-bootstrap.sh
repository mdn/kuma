#!/bin/bash
# Quick bootstrap script for a Centos 5.5 linux host
#
# Usage: 
#   export HOST={IP address of your Centos 5.5 host}
#   ssh root@$HOST 'wget --no-check-certificate -O- https://github.com/lmorchard/kuma/raw/HEAD/scripts/centos55-bootstrap.sh | bash'

GIT_REPO_URL="git://github.com/lmorchard/kuma.git"

# Need the EPEL repo right away, for git and puppet
rpm -Uvh http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm
yum install -y git puppet

# Clone the project from github
git clone $GIT_REPO_URL /vagrant
cd /vagrant

# I like to git push from my laptop to the dev VM, and this makes it easier
git config --local receive.denyCurrentBranch ignore
echo 'unset GIT_DIR && cd .. && git reset --hard' > .git/hooks/post-receive
chmod +x .git/hooks/post-receive

# Let puppet take it from here...
puppet /vagrant/puppet/manifests/*.pp
