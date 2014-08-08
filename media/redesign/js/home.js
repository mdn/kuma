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

})(jQuery);
