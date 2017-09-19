(function($) {
    'use strict';

    /*
        Auto-submit the filters form on the search page when a checkbox is changed.
    */
    $('.search-results-filters').on('change', 'input', function() {
        if (this.value !== 'none') {
            // De-select the All Topics checkbox when another filter is selected
            $('#no_filter').attr('checked', false);
        }
        $('#search-form').submit();
        $(this).parents('fieldset').attr('disabled', 'disabled');
    });

})(jQuery);
