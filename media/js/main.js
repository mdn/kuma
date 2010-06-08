(function () {
    $(document).ready(function() {
        /* Focus form field when clicking on error message. */
        $('#content-inner ul.errorlist a').click(function () {
                $($(this).attr('href')).focus();
                return false;
            });
    });
})();


/**
 * Handles autofill of text with default value. When an input field
 * is empty, the default value will be set on blur. Then, when focused,
 * the value will be set to empty.
 */
jQuery.fn.autoFillHelpText = function (text) {
    var colors = ['#9b9b9b',  // default value grayed out
                  '#333'];    // focus value

    if ($(this).val() == '' || $(this).val() == text) {
        $(this).val(text).css('color', colors[0]);
    }
    $(this).focus(function() {
        if ($(this).val() == text)
            $(this).val('').css('color', colors[1]);
    })
    .blur(function() {
        if ($(this).val() == '')
            $(this).val(text).css('color', colors[0]);
    });
};
