(function($) {
    'use strict';

    // Create the demos slider
    var $list = $('.home-demos-list');
    if ($list.length) {
        $list.owlCarousel({
            lazyLoad: true
        });
        $list.css('height', 'auto');
    }

    // Track search submissions with Optimizely
    var $centerSearchBox = $('#home-search-form');
    if ($centerSearchBox) {
        $centerSearchBox.submit(function() {
            mdn.optimizely.push(['trackEvent', 'submit-homepage-search-form']);
        });
    }

})(jQuery);
