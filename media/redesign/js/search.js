(function($) {
    'use strict';

    /*
        Auto-submit the filters form on the search page when a checkbox is changed.
    */
    $('.search-results-filters').on('change', 'input', function() {
        $('#search-form').submit();
        $(this).parents('fieldset').attr('disabled', 'disabled');
    });

})(jQuery);
