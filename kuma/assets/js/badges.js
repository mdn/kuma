(function (win, $) {
    'use strict';

    // Show the dialog immediately if the new badge is present!
    (function() {
            var $badgesTray = $('#badges-tray');
            var showFn = function() {
                $badgesTray.removeClass('show');
            };
            var timeout;
            var delay = 5000;

            if($badgesTray.length) {
                $badgesTray.addClass('show');
                timeout = setTimeout(showFn, delay);
            }

            $badgesTray
                .on('mouseenter', function() {
                    clearTimeout(timeout);
                })
                .on('mouseleave', function() {
                    setTimeout(showFn, delay / 2);
                })
                .on('transitionend webkitTransitionEnd', function(a, b, c) {
                    if(!parseInt($badgesTray.css('opacity'), 10)) {
                        $badgesTray.addClass('hidden');
                    }
                });
    })();

    $('form.obi_issuer button.issue').on('click', function() {
            // Grab the hosted assertion URL from the header link.
            var assertion_url = $('head link[rel="alternate"][type="application/json"]').attr('href');
            // Fire up the backpack lightbox.
            win.OpenBadges.issue([assertion_url], function (errors, successes) {
                if (errors.length) {
                        // TODO: Do something better here.
                        // window.alert("Failed to add award to your backpack.");
                        console.log('Failed to add award to backpack');
                }
                if (successes.length) {
                        // TODO: Do something... at all?
                        console.log('Award successfully added to backpack');
                }
            });
            return false;
    });

})(window, jQuery);
