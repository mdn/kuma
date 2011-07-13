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
        langs:  before => Stage[deki];
        deki:   before => Stage[main];
        deki_post:  require => Stage[main];
        hacks_post: require => Stage[deki_post];
    }

    class {

        dev_hacks: stage => hacks;

        repos: stage => pre;

        dev_tools: stage => basics;
        apache:    stage => basics;
        mysql:     stage => basics;
        memcache:  stage => basics;

        python: stage => langs;
        php:    stage => langs;

        dekiwiki: stage => deki;

        site_config: ;
        dekiwiki_config: stage => deki_post;
        dev_hacks_post: stage => hacks_post;

    }

}

include dev
