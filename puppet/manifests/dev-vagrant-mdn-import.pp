#
# Dev server data import for MDN
#
# Downloads hopefully recent anonymized exports from production databases and
# imports the data into mysql, with a few tweaks to ensure the dev box works.
#

$PROJ_DIR = "/vagrant"

class wikidb_import {
    exec { "wikidb_dump_download":
        cwd => "$PROJ_DIR/puppet/cache",
        timeout => 3600, # Too long, but this can take awhile
        command => "/usr/bin/wget http://people.mozilla.com/~lorchard/mdn_wikidb.sql.gz",
        creates => "$PROJ_DIR/puppet/cache/mdn_wikidb.sql.gz";
    }
    exec { "wikidb_import_dump":
        cwd => "$PROJ_DIR/puppet/cache",
        timeout => 3600, # Too long, but this can take awhile
        require => Exec["wikidb_dump_download"],
        command => "/bin/gzip -dc $PROJ_DIR/puppet/cache/mdn_wikidb.sql.gz | /usr/bin/mysql -uroot wikidb";
    }
}

class django_import {
    exec { "django_dump_download":
        cwd => "$PROJ_DIR/puppet/cache",
        timeout => 3600, # Too long, but this can take awhile
        command => "/usr/bin/wget http://people.mozilla.com/~lorchard/mdn_django.sql.gz",
        creates => "$PROJ_DIR/puppet/cache/mdn_django.sql.gz";
    }
    exec { "django_import_dump":
        cwd => "$PROJ_DIR/puppet/cache",
        timeout => 3600, # Too long, but this can take awhile
        require => Exec["django_dump_download"],
        command => "/bin/gzip -dc $PROJ_DIR/puppet/cache/mdn_django.sql.gz | /usr/bin/mysql -uroot kuma";
    }
}

class postimport_fixes {
    exec { "import_postdump":
        cwd => "$PROJ_DIR/puppet/cache",
        timeout => 3600, # Too long, but this can take awhile
        command => "/bin/cat ../files/tmp/postimport.sql | /usr/bin/mysql -uroot";
    }
}

class dev_import {
    include django_import, wikidb_import, postimport_fixes
    Class[django_import] -> Class[wikidb_import] -> Class[postimport_fixes]
}

include dev_import
