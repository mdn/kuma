/** JS enhancements for Demo Room */
$(document).ready(function () {

    $('.comment_reply').each(function () {

        var el = $(this);
        
        // Wire up reply form reveal link in threaded comments.
        el.find('.show_reply').click(function () {
            el.find('form').slideDown();
            return false;
        });

        // Quick and dirty validation for non-empty comment form.
        el.find('form').submit(function () {
            if ($(this).find('textarea').val().length == 0) {
                return false;
            }
            return true;
        });


    });

});
