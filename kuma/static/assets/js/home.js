(function($) {
    'use strict';

    // Create the demos slider
    $('.home-demos-list').css('height', 'auto').owlCarousel({ lazyLoad: true });

    // Track search submissions with Optimizely
    $('#home-search-form').on('submit', function() {
        mdn.optimizely.push(['trackEvent', 'submit-homepage-search-form']);
    });

})(jQuery);
