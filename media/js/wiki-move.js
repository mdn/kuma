(function($) {
     // Retrieve request and move information
     var $moveSlug = $('#moveSlug'),
         $suggestionInput = $('#parentSuggestion'),
         $suggestionContainer= $('.parentSuggestContainer'),
         $lookupLink = $('.moveLookupLink'),
         specific_slug = $('#currentSlug').val(),
         moveLocale = $('#moveLocale').val(),
         onHide = function() {
             $suggestionContainer.removeClass('show');
             $moveSlug[0].focus();
             $suggestionInput.mozillaAutocomplete('clear');
             $suggestionInput.attr('disabled', 'disabled');
         };

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
     $lookupLink.click(function(e) {
         e.preventDefault();
         // Show the lookup
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

     // Help on the client side for validating slugs to be moved
     var moveRegex = new RegExp($moveSlug.attr('data-validator'), 'i');
     $moveSlug.on('change keyup focus blur', function() {
        this.value = $.slugifyString(this.value.replace(moveRegex, ''), true);
     });
})(jQuery);