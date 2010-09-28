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
 * Handles autofill of text with default value for browsers that don't
 * support the HTML5 `placeholder` functionality.
 *
 * When an input field is empty, the default value (from `placeholder`
 * attribute) will be set on blur. Then, when focused, the value will
 * be set to empty.
 *
 */
 jQuery.fn.autoPlaceholderText = function () {

    // check for html5 placeholder support and fallback to js solution
    if (!Modernizr.input.placeholder) {

        function onFocus() {
            var $this = $(this);
            if ($this.val() === $this.attr('placeholder')) {
                $this.val('').addClass('placeholder-focused');
            }
        }

        function onBlur() {
            var $this = $(this);
            if ($this.val() === '') {
                $this.val($this.attr('placeholder')).removeClass('placeholder-focused');
            }
        }

        this.each(function () {
            var $this = $(this);
            var placeholder = $this.attr('placeholder');
            if (placeholder) {
                if (!$this.val() || $this.val() === placeholder) {
                    $this.val(placeholder).addClass('input-placeholder');
                }
                $this.focus(onFocus).blur(onBlur);
            }
        });

    }

    return this;
};
