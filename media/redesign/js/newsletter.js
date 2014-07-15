(function($) {
    'use strict';

    var $parent = $('#apps-newsletter-subscribe');
    var $checkbox = $('#newsletter-toggle').find('input:checkbox');
    var $settings = $parent.find('.newsletter-setting');
    var $agree = $settings.filter('.agree').find('input:checkbox');
    var required = 'required';

    if(!$checkbox.is(':checked')) {
        $settings.hide(0);
        $agree.removeAttr(required);
    }

    $checkbox.on('click', function() {
        if($checkbox.is(':checked')) {
            $settings.fadeIn();
            $agree.attr(required, required);
        } else {
            $settings.fadeOut();
            $agree.removeAttr(required);
        }
    });
})(jQuery);
