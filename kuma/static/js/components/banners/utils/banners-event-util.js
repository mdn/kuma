(function() {
    'use strict';
    var mdnBannerEvents = {
        /**
         * Attach common event handlers for the CTA banner.
         * @param {Object} banner - The banner element
         */
        attachEvents: function(banner) {
            this.handleCollapseEvent(banner);
            this.handleCloseEvent(banner);
        },
        /**
         * Handles click events on the close(x) icon
         * @param {Object} banner - The banner element
         */
        handleCloseEvent: function(banner) {
            var closeButton = banner.querySelector('.mdn-cta-close');

            if (!closeButton) {
                return;
            }

            closeButton.addEventListener('click', function() {
                banner.classList.add('hidden');
                window.mdnBannersStateUtil.setBannerInactive(
                    banner.dataset['banner']
                );
            });
        },
        /**
         * Handles click events on the collapse icon
         * @param {Object} banner - The banner element
         */
        handleCollapseEvent: function(banner) {
            var collapseButton = banner.querySelector('.mdn-cta-collapse');

            if (!collapseButton) {
                return;
            }

            collapseButton.addEventListener('click', function() {
                banner.classList.remove('expanded');
                banner.classList.add('is-collapsed');
            });
        }
    };

    /* First step towards using actual modules for our JS.
       This will allow unit testing with Jest */
    if (typeof exports === 'object') {
        module.exports = mdnBannerEvents;
    }

    window.mdnBannerEvents = mdnBannerEvents;
})();
