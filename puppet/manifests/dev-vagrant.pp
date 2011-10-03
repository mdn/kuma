#
# Dev server for MDN - includes Django, Dekiwiki
#

import "classes/*.pp"

$PROJ_DIR = "/vagrant"

$DB_NAME = "kuma"
$DB_USER = "kuma"
$DB_PASS = "kuma"

class dev {

    stage {
        hacks:  before => Stage[pre];
        pre:    before => Stage[basics];
        basics: before => Stage[langs];
        langs:  before => Stage[main];
        hacks_post: require => Stage[main];
    }

    class {

        dev_hacks: stage => hacks;

        repos: stage => pre;

        dev_tools: stage => basics;
        apache:    stage => basics;
        mysql:     stage => basics;
        memcache:  stage => basics;
        sphinx:    stage => basics;

        python: stage => langs;
        php:    stage => langs;

        site_config: ;
        dev_hacks_post: stage => hacks_post;

    }

}

include dev

