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
        // Setup the placeholder text
        $('#support-search input[name="q"]').autoPlaceholderText();

        // Submit the form on Enter
        $input.keyup(function(ev) {
            if(ev.keyCode === 13 && $input.val()) {
                $('#support-search form').submit();
            }
        });
    }

    $(document).ready(init);

}(jQuery));
