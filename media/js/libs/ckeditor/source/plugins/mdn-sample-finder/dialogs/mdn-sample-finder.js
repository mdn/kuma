'use strict';

CKEDITOR.dialog.add('mdn-sample-finder', function(editor) {

  var topLabel = gettext('Sample Finder'),
    docInfo = window.documentInfo,
    autoCompleteUrl = mdn.wiki.autosuggestTitleUrl,
    autoCompleteTextbox,
    $autoCompleteTextbox,
    autoCompleteItem,
    sectionsSelect,
    sectionsSelectParent;

  function toggleSelectDisplay(show) {
    jQuery(sectionsSelectParent).css("display", show ? "block": "none");
  }

  function updateSelectOptions(items) {
    clearSelect();
    sectionsSelect.add(gettext('Select a section'), '', 0);
    jQuery.each(items, function() {
      sectionsSelect.add(this.title, this.id);
    });
  }

  function clearSelect() {
    sectionsSelect.clear();
  }

  return {
    title: topLabel,
    minWidth: 350,
    minHeight: 230,
    contents: [
      {
        id: 'info',
        label: topLabel,
        title: topLabel,
        elements :
        [
          {
            id: 'url',
            type: 'text',
            label: gettext('Document'),
            'default': '',
            setup: function( data )
            { 
              // Do the moz autocomplete stuff
              if(!autoCompleteTextbox) {

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
                    autoCompleteItem = item;
                    // Update the dropdown list
                    if(item.sections.length) {
                      // Add items to the list
                      updateSelectOptions(item.sections);
                      toggleSelectDisplay(1);
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
            commit: function( data )
            {
              data.type = this.getValue();
            }
          },
          {
            type: 'vbox',
            id: 'attachment',
            children: [ {
              type: 'select',
              label: gettext('Sections in Document'),
              items: [],
              setup: function(data) {
                sectionsSelect = this;
                sectionsSelectParent = sectionsSelect.getElement().$;

                toggleSelectDisplay(0);
                clearSelect();
              },
              validate: function() {
                if(!jQuery(sectionsSelect.getInputElement().$).val()) {
                  return false;
                }
              }
            } ]
          }
        ]
      }
    ],

    onShow: function() {
      this.setupContent();

      if(docInfo && docInfo.sections.length) {
        $autoCompleteTextbox.val(docInfo.title);
        updateSelectOptions(docInfo.sections);
        toggleSelectDisplay(1);
        sectionsSelect.getInputElement().$.focus();
      }

      autoCompleteItem = null;
    },

    onOk: function() {
      var section = jQuery(sectionsSelect.getInputElement().$).val();
      if(section) {
        var value = "{{ EmbedLiveSample('" + section + "', '', '', ''";
        if(autoCompleteItem) {
          value += ", '" + autoCompleteItem.slug + "'";
        }
        value += ') }}';

        var element = new CKEDITOR.dom.element('p', editor.document);
        element.setText(value);
        editor.insertElement(element);
      }
    },

    onFocus: function() {
      var urlElement = this.getContentElement('info', 'url');
      urlElement.focus();
    }
  };
});