'use strict';

CKEDITOR.plugins.add('mdn-attachment', {
  onLoad: function() {
    // Utility method for updating the attachments dropdown
    // Should be used within the mdn-link and image dialogs
    mdn.ckeditor.updateAttachments = function(select, url, filter) {
      if(!select) return;

      var attachmentsArray = [],
        mdnArray = mdn.wiki.attachments,
        validFiles = {};

      // Clear the select
      select.clear();
      if(mdnArray) {
        // Clone the original array so we can sort
        mdnArray = mdnArray.slice(0);

        // Sort uploads by title ASC
        mdnArray.sort(function(a, b) {
          var aTitle = a.title.toLowerCase(),
            bTitle = b.title.toLowerCase();

          if (aTitle < bTitle) { //sort string ascending
            return -1;
          }
          else if (aTitle > bTitle) {
            return 1;
          }
          return 0;
        });

        // Cycle through, filter out cruft
        jQuery.each(mdnArray, function() {
          if(!filter || filter(this)) {
            if(!attachmentsArray.length) {
              select.add(gettext('Select an attachment'), '', 0);
            }
            attachmentsArray.push(this);
            select.add(this.title, this.url);
            validFiles[this.url] = this;
          }
        });
      }

      // Populate the dropdown
      if(!attachmentsArray.length) {
        select.add(gettext('No attachments available'), '', 0);
      }
      else if(validFiles[url]) {
        select.setValue(url);
      }
    };

    // Utility method to get an MDN attachment object by url
    mdn.ckeditor.getObjectByUrl = function(url) {
      var attachments = mdn.wiki.attachments;

      if(!attachments) return;

      var returnObj = false;
      $.each(attachments, function() {
        if(this.url == url) {
          returnObj = this;
        }
      });
      return returnObj;
    };
  }
});