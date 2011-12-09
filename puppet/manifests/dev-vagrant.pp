#
# Dev server for MDN
#

import "classes/*.pp"

$PROJ_DIR = "/vagrant"

$DB_NAME = "kuma"
$DB_USER = "kuma"
$DB_PASS = "kuma"

class dev {

    stage {
        hacks:  before => Stage[pre];
        pre:    before => Stage[tools];
        tools:  before => Stage[basics];
        basics: before => Stage[langs];
        langs:  before => Stage[vendors];
        vendors:   before => Stage[main];
        vendors_post:  require => Stage[main];
        hacks_post: require => Stage[vendors_post];
    }

    class {

        dev_hacks: stage => hacks;

        repos: stage => pre;

        dev_tools: stage => tools;

        apache:    stage => basics;
        mysql:     stage => basics;
        memcache:  stage => basics;
        sphinx:    stage => basics;

        python: stage => langs;
        php:    stage => langs;

        dekiwiki: stage => vendors;

        site_config: ;
        dekiwiki_config: stage => vendors_post;
        dev_hacks_post: stage => hacks_post;

    }

}

include dev
