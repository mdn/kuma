(function($) {
    'use strict';

    var $form = $('#wiki-page-edit');
    var $idTagsField = $('#tagit_tags');

    // Create a hidden input type for the purposes of saving
    var hiddenTags = $('<input type="hidden" name="tags" id="hiddenTags" value="' + ($idTagsField.val() || '') +    '" />').appendTo('#page-tags');

    // Grabs text from the list items, updates hidden input so tags are properly saved
    // Requires node reading because the tag-it widget incorrectly overrides the "singleNodeField"
    function consolidateTags(isRemove) {
        return function(e, li) {
            var listItems = $('#page-tags .tagit-choice');
            var itemTexts = [];

            // Don't add list items we're going to remove
            if(!isRemove) {
                listItems.push(li);
            }

            // Cycling through each list item,
            listItems.each(function() {
                if(!(isRemove && this === li[0])) {
                    itemTexts.push('"' + $(this).find('.tagit-label').text() + '"');
                }
            });
            hiddenTags.val(itemTexts.join(','));

            // Check whether there are net changes in tags
            if (undefined !== originalTags && hiddenTags.val() !== originalTags) {
                $('#page-tags').addClass('dirty').trigger('mdn:dirty');
            } else {
                $('#page-tags').removeClass('dirty').trigger('mdn:clean');
            }
        };
    }

    // Turn the text input into the widget
    $idTagsField.tagit({
        availableTags: mdn.wiki.tagSuggestions || [],
        singleField: true,
        allowSpaces: true,
        singleFieldNode: $idTagsField,
        onTagAdded    : consolidateTags(),
        onTagRemoved: consolidateTags(true)
    });

    // Set the new tag element text
    $('.tagit-new input').attr('placeholder', gettext('New tag...'));

    // Remove the hidden field since it wont be submitted anyways
    $idTagsField.remove();

    // Keep track of tag dirtiness
    var originalTags = hiddenTags.val();
    $form.on('mdn:save-success', function() {
        originalTags = hiddenTags.val();
    });

})(jQuery);
