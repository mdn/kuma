(function (win, $) {
    'use strict';

        var $cta = $('.cta:not(a)');
        var $cta_links = $cta.find('a');
        // allow focus
        $cta.attr('tabindex', 0).addClass('js');
        // when activated add the class to show and remove listeners which preventDefault
        function activate(caller) {
            var $caller = $(caller);
            var $calling_cta;
            if($caller.hasClass('cta')){
                $calling_cta = $caller;
            } else {
                $calling_cta = $caller.parents('.cta');
            }
            $calling_cta.addClass('active').off();
            $calling_cta.find('a').off();
        }
        // listen for tap
        $cta.on('focus', function() {
            activate(this);
        });
        // listen for focus
        $cta_links.on('touchstart', function(event) {
            event.preventDefault();
            activate(this);
        });

})(window, jQuery);
