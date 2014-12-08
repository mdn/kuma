'use strict';

CKEDITOR.dialog.add('mdn-redirect', function(editor) {
  var topLabel = gettext('MDN Redirect'),
    docInfo = window.documentInfo,
    autoCompleteUrl = mdn.wiki.autosuggestTitleUrl,
    autoCompleteTextbox,
    $autoCompleteTextbox;

  return {
    title: topLabel,
    minWidth: 350,
    minHeight: 230,
    contents: [
      {
        id: 'info',
        label: topLabel,
        title: topLabel,
        elements: [
          {
            id: 'autoselect',
            type: 'text',
            label: gettext('Document'),
            'default': '',
            setup: function( data ) { 
              // Do the moz autocomplete stuff
              if(!autoCompleteTextbox) {
                var self = this;

                // Get the INPUT node
                autoCompleteTextbox = this.getElement().getElementsByTag('input').$[0];

                // Create the autocompleter
                $autoCompleteTextbox = jQuery(autoCompleteTextbox);
                $autoCompleteTextbox.mozillaAutocomplete({
                  minLength: 1,
                  requireValidOption: true,
                  _renderItemAsLink: true,
                  styleElement: autoCompleteTextbox.parentNode,
                  autocompleteUrl: autoCompleteUrl,
                  onSelect: function(item, isSilent) {
                    // Update the dropdown list
                    if(item.url) {
                      // Add items to the list
                      self.getDialog().getContentElement( 'info', 'url' ).setValue(item.url);
                    }
                  },
                  buildRequestData: function(req) {
                    req.current_locale = 1;
                    return req;
                  }
                });
              }

              // Clear out the the values so there aren't any problems
              jQuery(autoCompleteTextbox).mozillaAutocomplete('clear');
            },
            commit: function(data) {
              data.type = this.getValue();
            }
          },
          {
            id: 'url',
            type: 'text',
            label: gettext('URL'),
            'default': ''
          }
        ]
      }
    ],

    onShow: function() {
      this.setupContent();
    },

    onOk: function(dialog) {
      var editor = dialog.sender.getParentEditor(),
        title = dialog.sender.getContentElement('info', 'autoselect').getValue(),
        url = dialog.sender.getContentElement('info', 'url').getValue(),
        pattern = mdn.ckeditor.redirectPattern;

      editor && title && url && editor.setData(
        pattern.replace('%(href)s', url).replace('%(title)s', title)
      );
    },

    onFocus: function() {
      var select = this.getContentElement('info', 'autoselect');
      select && select.focus();
    }
  };
});