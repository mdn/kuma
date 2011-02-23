/* Global initialization script */

$(document).ready(function() {
    $('body').addClass('hasJS');

    // Set up input placeholders.
    $('input[placeholder]').placeholder();

    // replace no-JS search with our built-in one
    var search = $('#site-search,#doc-search');
    if (search.length) search.attr('action', search.attr('data-url'))
          .removeAttr('data-url')
          .children('input[name=sitesearch]').remove();

    // Submit locale form on change
    $('form.languages')
        .find('select').change(function(){
            this.form.submit();
        });
});

/* Fake the placeholder attribute since Firefox doesn't support it. */
jQuery.fn.placeholder = function(new_value) {

    if (new_value) {
        this.attr('placeholder', new_value);
    }

    /* Bail early if we have built-in placeholder support. */
    if ('placeholder' in document.createElement('input')) {
        return this;
    }

    if (new_value && this.hasClass('placeholder')) {
        this.val('').blur();
    }

    return this.focus(function() {
        var $this = $(this),
            text = $this.attr('placeholder');

        if ($this.val() == text) {
            $this.val('').removeClass('placeholder');
        }
    }).blur(function() {
        var $this = $(this),
            text = $this.attr('placeholder');

        if ($this.val() == '') {
            $this.val(text).addClass('placeholder');
        }
    }).each(function(){
        /* Remove the placeholder text before submitting the form. */
        var self = $(this);
        self.closest('form').submit(function() {
            if (self.hasClass('placeholder')) {
                self.val('');
            }
        });
    }).blur();
};
