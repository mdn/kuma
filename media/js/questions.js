/*
 * questions.js
 * Scripts for the questions app.
 */

(function($){

    function init() {
        initSearch();
    }

    /*
     * Initialize the search widget
     */
    function initSearch() {
        var $input = $('#support-search input[name="q"]');

        // check for html5 placeholder support and fallback to js solution
        if (!Modernizr.input.placeholder) {
            $input.autoFillHelpText($input.attr('placeholder'));
        }

        // submit the form on Enter
        $input.keyup(function(ev) {
            if(ev.keyCode === 13 && $input.val()) {
                $('#support-search form').submit();
            }
        });
    }

    $(document).ready(init);

}(jQuery));
