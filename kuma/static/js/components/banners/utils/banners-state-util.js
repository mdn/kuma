(function() {
    'use strict';
    /**
     * Array of all banner ids
     * @const
     */
    var ALL_BANNER_IDS = ['developer_needs', 'contrib_beta'];
    /**
     * Length of time a banner remains hidden after it's been disabled
     * by clicking the close button.
     * @const
     */
    var BANNER_DISABLED_EXPIRATION = 5 * 24 * 60 * 60 * 1000; // 5 days.
    /**
     * A simple string to use as a namespace for `localStorage` items
     * @const
     */
    var LOCALSTORAGE_NAMESPACE = 'mdnBanner.';
    var mdnBannersStateUtil = {
        /**
         * Filters the `ALL_BANNER_IDS` down to only those in an active waffle flag state
         * @returns {Array} of banner ids or an empty array if no active banners
         */
        getWaffleEnabledBanners: function() {
            var activeBannerIds = [];

            if (window.waffle) {
                // both banners are currently controlled via waffle
                activeBannerIds = ALL_BANNER_IDS.filter(function(id) {
                    return window.waffle.flag_is_active(id);
                });
            }

            return activeBannerIds;
        },
        /**
         * Detrmines whether the `banner` is currently active.
         * @param {String} banner - The key identifier for the banner
         * @returns {Boolean} based on `localStorage` state
         */
        isBannerActive: function(banner) {
            if (window.mdn.features.localStorage) {
                try {
                    var item = localStorage.getItem(
                        LOCALSTORAGE_NAMESPACE + banner
                    );

                    /* If the banner was not found in `localStorage`,
                       it is currently active. */
                    if (item === null) {
                        return true;
                    }

                    var now = Date.now();
                    item = JSON.parse(item);
                    /* The banner was found in `localStorage`. Determine if it
                       should still be disabled */
                    if (item.timestamp + BANNER_DISABLED_EXPIRATION < now) {
                        // Disabled period has expired, remove from `localStorage`
                        this.setBannerActive(banner);
                        return true;
                    }

                    // banner is disabled
                    return false;
                } catch (error) {
                    console.error('Error while getting banner state: ', error);
                    return false;
                }
            }
            // banners are not supported in browsers that do not support localStorage
            return false;
        },
        /**
         * Set the banner state to active by removing the item from `localStorage`.
         * @param {String} banner - The key identifier for the banner
         */
        setBannerActive: function(banner) {
            if (banner === undefined) {
                throw 'setBannerActive: The banner property is required';
            }

            if (window.mdn.features.localStorage) {
                try {
                    localStorage.removeItem(LOCALSTORAGE_NAMESPACE + banner);
                } catch (error) {
                    console.error(
                        'Error while setting banner active state: ',
                        error
                    );
                }
            }
        },
        /**
         * Set the banner to an inactive state by setting a `localStorage`
         * item with a `timestamp` property set to the current date and time.
         * @param {String} banner - The key identifier for the banner
         */
        setBannerInactive: function(banner) {
            if (banner === undefined) {
                throw 'setBannerInactive: The banner property is required';
            }

            if (window.mdn.features.localStorage) {
                try {
                    var item = JSON.stringify({
                        // Sets the timestamp to today so we can check its expiration subsequent each page load.
                        timestamp: new Date().getTime()
                    });
                    localStorage.setItem(LOCALSTORAGE_NAMESPACE + banner, item);
                } catch (error) {
                    console.error(
                        'Error while setting banner inactive state: ',
                        error
                    );
                }
            }
        }
    };

    /* First step towards using actual modules for our JS.
       This will allow unit testing with Jest */
    if (typeof exports === 'object') {
        module.exports = mdnBannersStateUtil;
    }

    window.mdnBannersStateUtil = mdnBannersStateUtil;
})();
