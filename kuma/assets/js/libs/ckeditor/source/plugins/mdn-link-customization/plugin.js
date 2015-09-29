'use strict';

CKEDITOR.plugins.add('mdn-link-customization', {
  requires: 'link,mdn-attachment',

  autoCompleteTextbox: null,
  autoCompleteSelection: null,
  originalHighlightedText: '',

  onLoad: function() {
    var that = this;

    CKEDITOR.on('dialogDefinition', function(evt) {
      var dialogName = evt.data.name,
        dialogDefinition = evt.data.definition;

      if (dialogName != 'link')
        return;

      dialogDefinition.removeContents('target');

      var infoTab = dialogDefinition.getContents('info');

      that.removeProtocolField(infoTab);
      that.addArticleNameField(infoTab);
      that.addAttachmentField(infoTab);
      that.customizeLinkText(dialogDefinition);
      that.loadSelectedTextIntoAutoCompleteTextbox(dialogDefinition);
    });
  },

  init: function(editor) {
    // We can't use attachment's setup callback, because it is executed
    // becure url's value is set. This event is fired after that.
    var that = this;
    editor.on('dialogShow', function(evt) {
      var dialog = evt.data;

      if (dialog.getName() != 'link')
        return;

      var select = dialog.getContentElement('info', 'attachment');

      mdn.ckeditor.updateAttachments(select, dialog.getValueOf('info', 'url'));

      that.originalHighlightedText = editor.getSelection().getSelectedText();
    });
  },

  removeProtocolField: function(infoTab) {
    infoTab.remove('protocol');

    var that = this,
      urlInput = infoTab.get('url'),
      origCommit = urlInput.commit;

    // Don't extract the protocol to the protocol field.
    urlInput.onKeyUp = function() {};
    // Allow using any protocol in the URL field.
    // To do that we pretend that user chose 'Other' protocol in the protocol field.
    urlInput.commit = function(data) {
      origCommit.call(this, data);
      data.url.protocol = '';
    };
    // Load all protocols (not only the known one) to the URL field.
    urlInput.setup = function(data) {
      var url;

      if (data.url) {
        url = data.url.url;
        if (data.url.protocol)
          url = data.url.protocol + url;

        this.setValue(url);
      } else {
        this.setValue(that.getDefaultSlug());
      }
    };
  },

  addArticleNameField: function(infoTab) {
    var that = this;

    infoTab.add({
      id: 'articleName',
      type: 'text',
      label: gettext('Article Title Lookup / Link Text'),
      setup: function() {
        // This happens upon every open, so need to make sure we don't keep creating new autocompleters!
        var dialog = this.getDialog(),
          listener,
          term;

        that.autoCompleteSelection = null;

        // Create widget if not done already
        if(!that.autoCompleteTextbox) {
          that.autoCompleteTextbox = this.getElement().getElementsByTag('input').$[0];

          jQuery(that.autoCompleteTextbox).mozillaAutocomplete({
            minLength: 1,
            requireValidOption: true,
            _renderItemAsLink: true,
            labelField: 'label',
            styleElement: that.autoCompleteTextbox.parentNode,
            autocompleteUrl: mdn.wiki.autosuggestTitleUrl,
            onSelect: function(item, isSilent) {
              that.autoCompleteSelection = item;
              dialog.setValueOf('info', 'url', item.url);
            },
            buildRequestData: function(req) {
              req.current_locale = 1;
              return req;
            }
          });
        }

        // Clear out the the values so there aren't any problems
        jQuery(that.autoCompleteTextbox).mozillaAutocomplete('clear');
      }
    }, 'urlOptions');
  },

  addAttachmentField: function(infoTab) {
    var that = this;

    infoTab.add({
      id: 'attachment',
      type: 'select',
      label: gettext('Attachments'),
      items: [],
      onChange: function() {
        this.getDialog().setValueOf('info', 'url', this.getValue());
      }
    }, 'articleName');
  },

  // Returns the default slug for the give page ("/{lang}/docs/")
  getDefaultSlug: function() {
    var lang = jQuery('html').attr('lang'),
      returnValue = '';
    if (lang) {
      returnValue = '/' + lang + '/docs/';
    }
    return returnValue;
  },

  // Use autocompleted value or value from the auto complete input
  // as a text of newly created link.
  customizeLinkText: function(dialogDefinition) {
    var that = this,
      origOnOk = dialogDefinition.onOk;

    dialogDefinition.onOk = function() {
      var editor = this.getParentEditor(),
        selectedElement = this._.selectedElement;

      origOnOk.call(this);

      // Change only new links' texts.
      if (selectedElement)
        return;

      var text;

      if(that.originalHighlightedText) {
        text = that.originalHighlightedText
      }
      else if (that.autoCompleteSelection) {
        text = that.autoCompleteSelection.title;
      } else if (that.autoCompleteTextbox.value) {
        text = that.autoCompleteTextbox.value;
      }

      if (text) {
        var link = editor.elementPath().contains('a');
        // Should not happen, but better be safe.
        if (!link)
          return;

        link.setText(text);

        var range = editor.createRange();
        range.selectNodeContents(link);
        editor.getSelection().selectRanges([ range ]);
      }
    };
  },

  loadSelectedTextIntoAutoCompleteTextbox: function(dialogDefinition) {
    var that = this,
      origOnFocus = dialogDefinition.onFocus;

    dialogDefinition.onFocus = function() {
      var editor = this.getParentEditor(),
        selection = editor.getSelection(),
        selectedText = selection.getSelectedText().replace('()', ''),
        selectedElement = selection.getSelectedElement(),
        $autoComplete = jQuery(that.autoCompleteTextbox);

      // If there's selected text but not an element, search for an article
      if(selectedText && !selectedElement) {
        $autoComplete.val(selectedText);
        that.autoCompleteTextbox.focus();
        that.autoCompleteTextbox.select();
        $autoComplete.mozillaAutocomplete('deselect');
        $autoComplete.mozillaAutocomplete('search', selectedText);
        return;
      }

      origOnFocus.call(this);
    };
  }
});
