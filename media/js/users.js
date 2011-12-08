/*
 * users.js
 * Make public emails clickable.
 */

(function () {
    function makeEmailsClickable() {
        // bail if no emails on page
        var $emails = $('.email');
        if ($emails.length === 0) {
            return false;
        }
        $emails.each(function () {
            var email_val = $(this).text();
            $a = $('<a/>').attr('href', 'mailto:' + email_val)
                          .html(email_val);
            $(this).html($a);
        });
    }

    function breakOutOfFrames() {
        if (top.location != self.location) {
            top.location = self.location.href;
        }
    }

    $(document).ready(function () {
        makeEmailsClickable();
        breakOutOfFrames();
    });

}());
