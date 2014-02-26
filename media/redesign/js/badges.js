(function ($) {

    // Show the dialog immediately if the new badge is present!
    var $badgesModalContent = $('#recent_badge_awards');
    if($badgesModalContent.length) {
        $('body').mozModal($badgesModalContent, {
            title: $badgesModalContent.attr('data-title'),
            classes: 'transparent',
            allowScroll: true
        });
    }

    $('form.obi_issuer button.issue').click(function () {
        // Grab the hosted assertion URL from the header link.
        var assertion_url =
            $('head link[rel="alternate"][type="application/json"]')
             .attr('href');
        // Fire up the backpack lightbox.
        OpenBadges.issue([assertion_url], function (errors, successes) {
            if (errors.length) {
                // TODO: Do something better here.
                // window.alert("Failed to add award to your backpack.");
            }
            if (successes.length) {
                // TODO: Do something... at all?
            }
        });
        return false;
    });

})(jQuery);
