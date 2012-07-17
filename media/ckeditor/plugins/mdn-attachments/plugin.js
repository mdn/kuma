CKEDITOR.plugins.add('mdn-attachments', {
        init: function(editor) {

        	// Utility method for updating the attachments dropdown
        	// Should be used within the mdn-link and image dialogs
        	CKEDITOR.mdn.updateAttachments = function(select, url, filter) {
        		if(!select) return;

				var attachmentsArray = [],
					mdnArray = window.MDN_ATTACHMENTS,
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
						return 0
					});

					// Cycle through, filter out cruft
					jQuery.each(mdnArray, function() {
						if(!filter || filter(this)) {
							attachmentsArray.push(this);
							select.add(this.title, this.url);
							validFiles[this.url] = this;
						}
					});
				}

				// Populate the dropdown
				if(!attachmentsArray.length) {
					select.add(gettext('No attachments available'), '');
				}
				else {
					select.add(gettext('Select an attachment'), '', 0);
				}
				select.setValue(url);
			}

        }
});