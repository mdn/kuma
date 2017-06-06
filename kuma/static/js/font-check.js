var mdn = window.mdn || {};

(function(mdn) {
    'use strict';

    var fonts = [
        {
            'name' : 'Open Sans',
            'className' : 'ffo-opensans',
            'loaded': false,
            'varient' : [
                {'weight' : 'normal'},
                {'weight' : 'bold'},
                {'style' : 'italic'}
            ]
        },
        {
            'name' : 'zillaslab',
            'className' : 'ffo-zillaslab',
            'loaded': false,
            'varient' : [
                {'weight' : 'normal'},
                {'weight' : 'bold'},
                {'style' : 'italic'}
            ]
        },
        {
            'name' : 'zillahighlight',
            'className' : 'ffo-zillahighlight',
            'loaded': false,
            'varient' : [
                {'weight' : 'normal'}
            ]
        }
    ];


    for (var i = 0, len = fonts.length; i < len; i++) {
        try {
            if (sessionStorage.getItem(fonts[i].name)) {
                // set attribute on <html> to trigger CSS changes
                document.documentElement.setAttribute('data-' + fonts[i].className, true);
                // inform fonts.js that this font is already loaded &
                // skip the FFO loading routine
                fonts[i].loaded = true;
            }
        } catch(e) {}
    }

    // expose fonts site-wide for use in fonts.js
    mdn.fonts = fonts;
})(mdn);
