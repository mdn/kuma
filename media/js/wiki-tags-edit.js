(function($) {
  $(document).ready(function() {

    var $idTagsField = $('#tagit_tags');

    // Create a hidden input type for the purposes of saving
    var hiddenTags = $('<input type="hidden" name="tags" id="hiddenTags" value="' + ($idTagsField.val() || '') +  '" />').appendTo('#page-tags');

    // Grabs text from the list items, updates hidden input so tags are properly saved
    // Requires node reading because the tag-it widget incorrectly overrides the "singleNodeField"
    function consolidateTags(isRemove) {
      return function(event, li) {
        var listItems = $('#page-tags .tagit-choice'),
            itemTexts = [];

        // Don't add list items we're going to remove
        if(!isRemove) listItems.push(li);

        // Cycling through each list item, 
        listItems.each(function(i, e, a) {
          if(isRemove && this == li[0]) {
            // do nothing -- this is the item being removed
          }
          else {
            itemTexts.push('"' + $(this).find('.tagit-label').text() + '"');
          }
        });
        hiddenTags.val(itemTexts.join(','));
      };
    };

    // Turn the text input into the widget
    $idTagsField.tagit({
      availableTags: mdn.wiki.tagSuggestions || [],
      singleField: true,
      allowSpaces: true,
      singleFieldNode: $idTagsField,
      onTagAdded  : consolidateTags(),
      onTagRemoved: consolidateTags(true)
    });
    
    // Set the new tag element text
    $('.tagit-new input').attr('placeholder', gettext('New tag...'));
    
    // Remove the hidden field since it wont be submitted anyways
    $idTagsField.remove();
  })
})(jQuery);