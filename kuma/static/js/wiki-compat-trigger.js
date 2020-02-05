(function(win, doc, $) {
    'use strict';

    /** Load and build compat tables if present in page */
    (function() {
        var compatCSS;
        var compatJS;

        // don't run if no compat table on page with min 1 row
        var $compatFeatureRows = $('.bc-table tbody tr');
        if(!$compatFeatureRows.length) {
            return;
        }

        // don't run if assests not available
        if(!win.mdn || !mdn.assets) {
            return;
        }

        /** This chaining logic will break in development if these assets are
            split into multiple files. */
        compatCSS = mdn.assets.css['wiki-compat-tables'][0];
        compatJS = mdn.assets.js['wiki-compat-tables'][0];
        $('<link />').attr({
            href: compatCSS,
            type: 'text/css',
            rel: 'stylesheet'
        }).on('load', function() {
            $.ajax({
                url: compatJS,
                dataType: 'script',
                cache: true
            }).then(function() {
                $('.bc-table').mozCompatTable();
            });

        }).appendTo(doc.head);
    })();

})(window, document, jQuery);
