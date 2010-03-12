$(document).ready(function() {
    // initiate tabs
    var tabs = $('#search-tabs').tabs()
    // TODO: use l10n
    // @see http://jbalogh.github.com/zamboni/#gettext-in-javascript
      , DEFAULT_AUTHOR = 'username'
      , DEFAULT_QUERY = 'crashes on youtube'
      , DEFAULT_TAGS = 'tag1, tag2'
    ;

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
    autoFillHelpText($('#search-tabs input[name="author"]'), DEFAULT_AUTHOR);
    autoFillHelpText($('#search-tabs input[name="q"]'), DEFAULT_QUERY);
    autoFillHelpText($('#search-tabs input[name="tag"]'), DEFAULT_TAGS);

    $("#tab-wrapper form").submit(function() {
      if ($('#search-tabs input[name="author"]').val() == DEFAULT_AUTHOR) {
        $('input[name="author"]').val('');
      }
      if ($('#search-tabs input[name="q"]').val() == DEFAULT_QUERY) {
        $('#search-tabs input[name="q"]').val('');
      }
      if ($('#search-tabs input[name="tag"]').val() == DEFAULT_TAGS) {
        $('#search-tabs input[name="tag"]').val('');
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