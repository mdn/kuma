# Ensure all necessary package repos are available.

class repos {
    # Make sure we've got EPEL for extra packages
    # see also: http://developer.mindtouch.com/en/docs/mindtouch_setup/010Installation/060Installing_on_CentOS
    $epel_url = "http://download.fedora.redhat.com/pub/epel/5/x86_64/epel-release-5-4.noarch.rpm"
    exec { "repo_epel":
        command => "/bin/rpm -Uvh $epel_url",
        creates => '/etc/yum.repos.d/epel.repo'
    }

    file { 
        # see also: http://developer.mindtouch.com/en/docs/mindtouch_setup/010Installation/060Installing_on_CentOS/Installing%2F%2FUpgrade_Mono_on_CentOS
        "repo_mono":
            path => "/etc/yum.repos.d/mono.repo",
            ensure => file,
            source => "/vagrant/puppet/files/etc/yum.repos.d/mono.repo",
            owner => "root", group => "root", mode => 0644;
        "repo_mindtouch":
            path => "/etc/yum.repos.d/mindtouch.repo",
            ensure => file,
            source => "/vagrant/puppet/files/etc/yum.repos.d/mindtouch.repo",
            owner => "root", group => "root", mode => 0644;
    }

}
