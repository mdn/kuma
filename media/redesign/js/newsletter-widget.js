var checkbox = '#apps-newsletter-subscribe #newsletter-signup';
var settings = '#apps-newsletter-subscribe .newsletter-setting';
var agree = '#apps-newsletter-subscribe #id_agree';

if(!$(checkbox).is(':checked')) {
    $(settings).hide(0);
    $(agree).removeAttr('required');
}

$(checkbox).click(function() {
    if($(checkbox).is(':checked')) {
        $(settings).fadeIn();
        $(agree).attr('required', 'required');
    } else {
        $(settings).fadeOut();
        $(agree).removeAttr('required');
    }
});
