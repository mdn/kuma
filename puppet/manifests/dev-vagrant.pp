# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

#
# Dev server for MDN
#

import "classes/*.pp"

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
        vendors:   before => Stage[extras];
        extras: before => Stage[main];
        vendors_post:  require => Stage[main];
        # Stage[main]
        hacks_post: require => Stage[vendors_post];
    }

    class {
        dev_hacks: stage => hacks;

        update_repos: stage => pre;

        dev_tools: stage => tools;

        apache:         stage => basics;
        mysql:          stage => basics;
        memcache:       stage => basics;
        rabbitmq:       stage => basics;
        elasticsearch:  stage => basics;

        nodejs: stage => langs;
        python: stage => langs;

        statsd:         stage => extras;

        site_config: stage => main;
        dev_hacks_post: stage => hacks_post;
    }

}

include dev
