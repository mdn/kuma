$(document).ready(function() {
    // initiate tabs
    var tabs = $('#search-tabs').tabs();
    var DEFAULT_AUTHOR = $('#default_author').val();
    var DEFAULT_QUERY = $('#default_query').val();
    var DEFAULT_TAGS = $('#default_tags').val();

    /**
     * Handles autofill of text with default value. When an input field
     * is empty, the default value will be set on blur. Then, when focused,
     * the value will be set to empty.
     */
    function autoFillHelpText(field, text) {
        if (field.val() == '' || $(field).val() == text) {
            field.val(text).css('color', '#9b9b9b');
        }
        field.focus(function() {
            if ($(this).val() == text)
                $(this).val('').css('color', '#333');
        })
        .blur(function() {
            if ($(this).val() == '')
                $(this).val(text).css('color', '#9b9b9b');
        });
    }
    autoFillHelpText($('input[name="author"]'), DEFAULT_AUTHOR);
    autoFillHelpText($('input[name="q"]'), DEFAULT_QUERY);
    autoFillHelpText($('input[name="tag"]'), DEFAULT_TAGS);

    $("#tab-wrapper form").submit(function() {
      if ($('input[name="author"]').val() == DEFAULT_AUTHOR) {
        $('input[name="author"]').val('');
      }
      if ($('input[name="q"]').val() == DEFAULT_QUERY) {
        $('input[name="q"]').val('');
      }
      if ($('input[name="tags"]').val() == DEFAULT_TAGS) {
        $('input[name="tags"]').val('');
      }
    });

    $('.datepicker').datepicker();

    $('select[name="created"]').change(function () {
        if ($(this).val() == 0)
            $('input[name="created_date"]').hide();
        else
            $('input[name="created_date"]').show();
    });
    $('select[name="created"]').change();
    $('.datepicker').attr('readonly', 'readonly').css('background', '#ddd');

    if ($('#where').val() == '2') {
        tabs.tabs('select', 1);
    }
});