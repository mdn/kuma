$(document).ready(function() {
    // initiate tabs
    var tabs = $('#search-tabs').tabs(),
        cache_search_date = $('.search-date');

    $('#search-tabs input[name="q"]').autoPlaceholderText();
    $('#search-tabs input[name="author"]').autoPlaceholderText();
    $('#search-tabs input[name="tags"]').autoPlaceholderText();

    $("#tab-wrapper form").submit(function() {
        var tabs = [$('#kb'), $('#support'), $('#discussion')], num_tabs = 3,
            fields = ['input[name="q"]', 'input[name="author"]',
                      'input[name="tags"]'],
            num_fields = fields.length, fi = 0, ti = 0, the_input;

        for (ti = 0; ti < num_tabs; ti++) {
            for (fi = 0; fi < num_fields; fi++) {
                the_input = $(fields[fi], tabs[ti]);
                if (the_input.length > 0 &&
                    the_input.val() == the_input.attr('placeholder')) {
                    the_input.val('');
                }
            }
        }
    });

    $('.datepicker').datepicker();
    $('.datepicker').attr('readonly', 'readonly').css('background', '#ddd');

    $('select', cache_search_date).change(function () {
        if ($(this).val() == 0) {
            $('input', $(this).parent()).hide();
        } else {
            $('input', $(this).parent()).show();
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
