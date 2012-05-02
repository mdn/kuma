$(document).ready(function() {
    // initiate tabs
    var tabs = $('#search-tabs').tabs(),
        cache_search_date = $('.showhide-input');

    $('#search-tabs input[name="q"]').autoPlaceholderText();
    $('#search-tabs input[name="author"]').autoPlaceholderText();
    $('#search-tabs input[name="tags"]').autoPlaceholderText();

    $('#tab-wrapper form').submit(function() {
        $('input.auto-fill').each(function() {
            var $this = $(this);
            if ($this.val() == $this.attr('placeholder')) {
                $this.val('');
            }
        });
    });

    // Create the datepicker
    $datePicker = $('.datepicker');
    $datePicker.datepicker();
    $datePicker.attr('readonly', 'readonly').css('background', '#ddd');

    // Force numeric input for num_votes
    $('input.numeric').numericInput();

    $('select', cache_search_date).change(function () {
        var $this = $(this),
            $input = $('input', $this.parent());

        if ($this.val() == 0) {
            $input.hide();
        } else {
            $input.show();
        }
        
    }).change();

    switch(parseInt($('#where').text(), 10)) {
        case 4:
            tabs.tabs('select', 2);
            break;
        case 2:
            tabs.tabs('select', 1);
            break;
        case 1:
        default:
            tabs.tabs('select', 0);
    }
});

/**
 * Accept only numeric keystrokes.
 *
 * Based on http://snipt.net/GerryEng/jquery-making-textfield-only-accept-numeric-values
 */
jQuery.fn.numericInput = function (options) {
    // Only works on <input/>
    if (!this.is('input')) {
        return this;
    }

    this.keydown(function(event) {
        // Allow only backspace and delete
        if ( event.keyCode == 46 || event.keyCode == 8 ) {
            // let it happen, don't do anything
        } else if (event.shiftKey || event.keyCode < 48 || event.keyCode > 57) {
            // Ensure that it is a number and stop the keypress
            event.preventDefault(); 
        }
    });


    return this;
};
