(function ($) {
    'use strict';

    var redesignNotice = document.getElementById('redesignNotice');

    if(!redesignNotice) {
        return;
    } else {
        if(mdn.features.localStorage) {
            // first visit to redesign?
            var seenNotice = localStorage.getItem('redesignNotice') === 'true' ? true : false;
            if (!seenNotice) {
                var $redesignNotice = $(redesignNotice);

                // wire close button
                $('#redesignHide').on('click', function() {
                    $redesignNotice.remove();
                });
                // show message
                $redesignNotice.prependTo($('#content'));
                $redesignNotice.removeClass('hidden');

                // set local storage they've seen it
                localStorage.setItem('redesignNotice', true);
            }
        }
    }
})(jQuery);
