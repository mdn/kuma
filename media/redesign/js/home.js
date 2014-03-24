(function($) {
    'use strict';

    // Create the demos slider
    var $list = $('.home-demos-list');
    $list.owlCarousel({
        lazyLoad: true
    });
    $list.css('height', 'auto');

})(jQuery);
