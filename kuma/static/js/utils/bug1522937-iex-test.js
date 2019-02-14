(function() {
    'use strict';

    var iexIframe;
    var url = document.location.href;
    var pageName = url.substr(url.indexOf('box-shadow'));

    if (pageName === 'box-shadow-display-none') {
        iexIframe = document.querySelector('.interactive');

        // just to be sure there is an iframe
        if (iexIframe) {
            iexIframe.classList.add('hidden');
        }
    } else if (pageName === 'box-shadow-display-none-empty-src') {
        iexIframe = document.querySelector('.interactive');
        // just to be sure there is an iframe
        if (iexIframe) {
            iexIframe.src = 'about:blank';
            iexIframe.classList.add('hidden');
        }
    } else {
        return;
    }
})();
