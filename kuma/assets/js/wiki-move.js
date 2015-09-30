(function($) {
    'use strict';

     // Retrieve request and move information
     var $moveSlug = $('#move-slug');
     var $suggestionInput = $('#parent-suggestion');
     var $suggestionContainer= $('.parent-suggest-container');
     var $lookupLink = $('.parent-suggest-link');
     var $previewUrl = $('#preview-url');
     var specific_slug = $('#current-slug').val();
     var moveLocale = $('#locale').val();
     var onHide = function() {
         $suggestionContainer.removeClass('show');
         $moveSlug[0].focus();
         $suggestionInput.mozillaAutocomplete('clear');
         $suggestionInput.attr('disabled', 'disabled');
     };
     var moveRegex = new RegExp($moveSlug.attr('data-validator'), 'i');

     // Hook up the autocompleter before creating the link connection
     $suggestionInput.mozillaAutocomplete({
         minLength: 1,
         requireValidOption: true,
         autocompleteUrl: mdn.wiki.autosuggestTitleUrl,
         _renderItemAsLink: true,
         buildRequestData: function(req) {
             req.locale = moveLocale;
             return req;
         },
         onSelect: function(item, isSilent) {
             $moveSlug.val(item.slug + '/' + specific_slug);
             if(!isSilent) {
                 onHide();
             }
         },
         onDeselect: function(item) {
             $moveSlug.val('');
         }
     });

     // Show the lookup when the link is clicked
     $lookupLink.on('click', function(e) {
         e.preventDefault();
         $suggestionContainer.addClass('show');
         $suggestionInput[0].disabled = false;
         $suggestionInput[0].focus();
     });

     // Hide lookup when the field is blurred
     $suggestionInput.on('blur', onHide);

     // Go to link when blured
     $moveSlug.on('blur', function() {
         $lookupLink.focus();
     });

     // Update the preview upon change
     $moveSlug.on('keyup', function() {
        var value = $(this).val() || $previewUrl.data('specific');
        $previewUrl.text($previewUrl.data('url') + value);
     });

     // Help on the client side for validating slugs to be moved
     $moveSlug.on('change keyup focus blur', function() {
        this.value = $.slugifyString(this.value.replace(moveRegex, ''), true, true);
     });
})(jQuery);
