#!/bin/bash
#
# Quick bootstrap script for a Centos 5.5 linux host
#
# Example Rackspace Cloud usage: 
#
#   * Grab a copy of [rscurl](https://github.com/jsquared/rscurl).
#       * You can use web-based management, but the command line can be fun.
#
#   * Spin up a server:
#       rscurl.sh -a $RACKSPACE_API_KEY -u $RACKSPACE_USERNAME -c create-server -f 2 -i 51 -n 'kuma-dev-1'
#
#   * Note the server IP and root password reported by Rackspace.
#
#   * Wait until server is active. Check like so:
#       rscurl.sh -a $RACKSPACE_API_KEY -u $RACKSPACE_USERNAME -c list-servers
#
#   * Once the server is active, kick off the bootstrap:
#       ssh root@$HOST 'wget --no-check-certificate -O- https://github.com/mozilla/kuma/raw/HEAD/scripts/centos55-bootstrap.sh | bash'
#

GIT_REPO_URL="git://github.com/mozilla/kuma.git"

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
puppet /vagrant/puppet/manifests/dev-vagrant.pp
