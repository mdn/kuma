(function () {
    $(document).ready(function() {
        /* Focus form field when clicking on error message. */
        $('#content-inner ul.errorlist a').click(function () {
                $($(this).attr('href')).focus();
                return false;
            });

        if (document.body.getAttribute('data-readonly') == 'true') {
            $forms = $('form[method=post]');
            $forms.find('input, button, select, textarea').attr('disabled', 'disabled');
            $forms.find('input[type=image]').css('opacity', .5);
        }

        initAutoSubmitSelects();
        initSearchAutoFilters();

    });

    /*
     * Initialize some selects so that they auto-submit on change.
     */
    function initAutoSubmitSelects() {
        $('select.autosubmit').change(function() {
            $(this).closest('form').submit();
        });
    }

    function initSearchAutoFilters() {
        var $browser = $('#browser'),
            $os = $('#os'),
            $search = $('.support-search form'),
            for_os = $.parseJSON($('body').attr('data-for-os')),
            for_version = $.parseJSON($('body').attr('data-for-version'));

        /**
         * (Possibly create, and) update a hidden input on new search forms
         * to filter based on Help With selections.
         */
        function updateAndCreateFilter(name, $source, data) {
            $search.each(function(i, el) {
                var $input = $(el).find('input[name='+name+']');
                if (!$input.length) {
                    $input = $('<input type="hidden" name="'+name+'">');
                    $(el).prepend($input);
                }
                $input.val(data[$source.val()]);
            });
        }

        if ($browser.length) {
            function updateBrowserFilter() {
                updateAndCreateFilter('fx', $browser, for_version);
            }
            updateBrowserFilter();
            $browser.change(updateBrowserFilter);
        }

        if ($os.length) {
            function updateOSFilter() {
                updateAndCreateFilter('os', $os, for_os);
            }
            updateOSFilter();
            $os.change(updateOSFilter);
        }
    }
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
