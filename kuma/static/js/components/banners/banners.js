(function() {
    'use strict';

    /**
     * This manages the display of CTA(Call to Action) banners on MDN
     * Web Docs. The logic for when to show, or not show, a banner
     * is defined in `utils\banners-state-util.js`
     */
    var mdnCtaBanner = {
        /**
         * Loops through the `bannersArray` and shows the first
         * active banner.
         * @param {Array} bannersArray - An array of active banner ids
         */
        show: function(bannersArray) {
            for (var i = 0, l = bannersArray.length; i < l; i++) {
                var bannerId = bannersArray[i];
                if (window.mdnBannersStateUtil.isBannerActive(bannerId)) {
                    var activeBanner = document.getElementById(bannerId);
                    activeBanner.classList.remove('hidden');
                    window.mdnBannerEvents.attachEvents(activeBanner);
                    return;
                }
            }
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
