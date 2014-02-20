#
# Dev server for MDN
#

import "classes/*.pp"

$DB_NAME = "kuma"
$DB_USER = "kuma"
$DB_PASS = "kuma"

Exec {
    # This is what makes all commands spew verbose output
    logoutput => true
}

class dev {

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
        elasticsearch: stage => basics;
        foreman: stage => basics;

        nodejs: stage => langs;
        python: stage => langs;

        stylus: stage => extras;

        site_config: stage => main;
        dev_hacks_post: stage => hacks_post;
    }

}

include dev
