//
// User detail and edit view enhancements
//
(function () {
    'use strict';

    var DEBOUNCE_DELAY = 25;

    // Translate multiple rapid calls to a function into a single call after a
    // short delay. Also serves to allow UI updates to complete due to yielding
    // the event loop.
    //
    // This seems to paper over some odd timing bugs where checkboxes aren't
    // detected, and certain events aren't caught.
    function debounce(func, wait, immediate) {
        var timeout;
        return function() {
            var context = this, args = arguments;
            var later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            var callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    }

    // Rebuild the list of expertise tags and checkboxes.
    var rebuildExpertiseTaglist = debounce(function () {
        var taglist = $('#tags-expertise');
        var interests = $('#id_user-interests');
        var i_tags = interests.val().split(",");

        // Completely rebuild the list of expertise tags. Seems wasteful, but
        // the number of elements should be relatively tiny vs the code to do
        // it more surgically.
        taglist.empty();
        $.each(i_tags, function (idx, tag) {
            tag = $.trim(tag);
            if(window.INTEREST_SUGGESTIONS.indexOf(tag) === -1) return;

            taglist.append('<li class="tag-expert">' +
                '<label for="expert-' + idx + '">' +
                '<input type="checkbox" name="expert-' + idx + '" ' +
                    'id="expert-'+idx+'" value="' + tag + '"> ' + tag +
                '</label></li>');
        });

        // Do this mutual update, so any checkboxes that have disappeared
        // also get removed from the field.
        updateTaglistFromField();
        updateFieldFromTaglist();
    });

    // Update the checked tags in expertise tag list from the text field
    var updateTaglistFromField = debounce(function () {
        var taglist = $('#tags-expertise');
        var expertise = $('#id_user-expertise');
        var eTags = expertise.val().split(',');

        $('#tags-expertise .tag-expert input[type=checkbox]').removeAttr('checked');
        $.each(eTags, function(idx, tag) {
            tag = $.trim(tag);
            $('#tags-expertise .tag-expert input[value=' + tag + ']').attr('checked', 'checked');
        });
    });

    // Update the expertise text field from checked boxes in tag list
    var updateFieldFromTaglist = debounce(function () {
        var tags = $('#tags-expertise .tag-expert input[type=checkbox]:checked')
            .map(function () { return $(this).val(); })
            .get().join(',');
        $('#id_user-expertise').val(tags);
    });

    $(document).ready(function(){

        // Convert interests text field into a tag-it widget
        $('#id_user-interests').hide()
            .after('<ul id="tagit-interests"></ul>')
            .change(rebuildExpertiseTaglist);

        $('#tagit-interests').tagit({
            availableTags: window.INTEREST_SUGGESTIONS,
            allowSpaces: true,
            singleField: true,
            singleFieldNode: $('#id_user-interests'),
            onTagAdded: rebuildExpertiseTaglist,
            onTagRemoved: rebuildExpertiseTaglist,
            onTagClicked: rebuildExpertiseTaglist
        });

        // Set the new tag element text
        $('#tagit-interests .tagit-new input').attr('placeholder', gettext('New interest...'));

        // Convert the expertise text field into tag list with checkboxes sync'd to
        // interests
        $("#id_user-expertise").hide().after("<ul id='tags-expertise' class='tags'></ul>");

        $('#tags-expertise').click(updateFieldFromTaglist);
        rebuildExpertiseTaglist();

        // word count
        $('.wordcount').each(function(i, el){

            var $el = $(el);
            var placeholder = $el.find('.counter');
            var limit = parseInt(placeholder.text(), 10);
            var currcount = 0;
            var field = $el.children('textarea');

            function updateWordCount() {
                var words = $.trim(field.val()).split(' ');
                var color = placeholder.parent().css('color');
                var invalidColor = '#900';
                var length;

                if(words[0] === ''){ words.length = 0; }
                currcount = limit - words.length;
                placeholder.text(currcount);

                length = words.length;

                if(length >= limit && color !== invalidColor) {
                    placeholder.parent().css('color', invalidColor);
                }
                else if(words.length < limit && color === invalidColor) {
                    placeholder.parent().css('color', '');
                }
            }

            updateWordCount();
            field.keypress(updateWordCount);
        });

        // Update "Other users", preventing "blank" submissions
        $('#users input').mozPlaceholder();
    });
})();
