(function ($) {
    'use strict';

    // allow focus and listen for tap
    $('.cta:not(a)').attr('tabindex', 0)
        .addClass('js')
        .on('focus touchstart', function(ev) {
            ev.preventDefault();
            activate(this);
        });

    // when activated add the class to show and remove listeners which preventDefault
    function activate(caller) {
        var $caller = $(caller);
        var $callingCta = $caller.hasClass('cta') ? $caller : $caller.parents('.cta');
        $callingCta.addClass('active').off();
        $callingCta.find('a').off();
    }

})(jQuery);
