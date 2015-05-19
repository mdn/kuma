#
# Dev server for MDN
#

import "classes/*.pp"
include apt

$DB_NAME = "kuma"
$DB_USER = "kuma"
$DB_PASS = "kuma"

Exec {
    # This is what makes all commands spew verbose output
    logoutput => true
}


class dev {
    apt::key { 'elasticsearch':
      key => 'D88E42B4',
      key_source => 'http://packages.elasticsearch.org/GPG-KEY-elasticsearch',
    }
    class { 'elasticsearch':
      package_url => 'https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-1.3.7.deb',
      java_install => true,
      java_package => 'openjdk-7-jre-headless',
    }

    elasticsearch::instance { 'kuma':
      datadir => '/var/lib/elasticsearch',
      config => {
        'node' => {
          'name' => 'kuma'
        },
        'index' => {
          'number_of_replicas' => '0',
          'number_of_shards'   => '1'
        },
        'network' => {
          'host' => '0.0.0.0'
        },
        'discovery.zen.ping' => {
            'multicast.enabled' => false,
            'unicast.hosts' => ['0.0.0.0']
        }
      },
    }


    elasticsearch::plugin{'mobz/elasticsearch-head':
      module_dir => 'head',
      instances => ['kuma'],
    }

    stage {
        hacks: before => Stage[pre];
        pre: before => Stage[basics];
        basics: before => Stage[langs];
        langs: before => Stage[vendors];
        vendors: before => Stage[extras];
        extras: before => Stage[main];
        vendors_post: require => Stage[main];
        # Stage[main]
        hacks_post: require => Stage[vendors_post];
    }

    class {
        dev_hacks: stage => hacks;

        basics: stage => basics;
        apache: stage => basics;
        mysql: stage => basics;
        memcache: stage => basics;
        rabbitmq: stage => basics;
        foreman: stage => basics;

        nodejs: stage => langs;
        python: stage => langs;

        stylus: stage => extras;
        cssmin: stage => extras;
        uglify: stage => extras;
        csslint: stage => extras;

        site_config: stage => main;
        dev_hacks_post: stage => hacks_post;
    }

}

include dev
