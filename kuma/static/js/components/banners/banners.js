(function() {
    'use strict';

    /**
     * This manages the display of CTA(Call to Action) banners on MDN
     * Web Docs. The logic for when to show, or not show, a banner
     * is defined in `utils/banners-state-util.js`
     */
    var mdnCtaBanner = {
        /**
         * Loops through the `bannersArray` and shows the first
         * active banner.
         * @param {Array} bannersArray - An array of active banner ids
         */
        show: function(bannersArray) {
            bannersArray.forEach(function maybeCloseBanner(bannerId) {
                if (window.mdnBannersStateUtil.isBannerActive(bannerId)) {
                    var activeBanner = document.getElementById(bannerId);
                    // If, for some other reason (e.g. archived pages),
                    // the banner, by that ID, is not in the DOM, then
                    // don't bother.
                    if (activeBanner) {
                        activeBanner.classList.remove('hidden');
                        window.mdnBannerEvents.attachEvents(activeBanner);
                    }
                }
            });
        }
    };

    /* First step towards using actual modules for our JS.
       This will allow unit testing with Jest */
    if (typeof exports === 'object') {
        module.exports = mdnCtaBanner;
    }

    window.mdnCtaBanner = mdnCtaBanner;

    window.addEventListener('load', function() {
        mdnCtaBanner.show(window.mdnBannersStateUtil.getWaffleEnabledBanners());
    });
})();
