$(document).ready(function () {
    var MAX_FILENAME_LENGTH = 20;  // max filename length in characters

    $('div.attachments-upload input[type="file"]').each(function() {
        $(this).uploadInput({
            url: $(this).closest('.attachments-upload').attr('data-post-url'),
            beforeSubmit: function(theInput) {
                var divUpload = theInput.closest('.attachments-upload'),
                    options = {
                        progress: divUpload.find('.upload-progress'),
                        add: divUpload.find('.add-attachment'),
                        adding: divUpload.find('.adding-attachment'),
                        loading: divUpload.find('.uploaded')
                    };

                // truncate filename
                options.filename = theInput.val().split(/[\/\\]/).pop()
                if (options.filename.length > MAX_FILENAME_LENGTH) {
                    options.filename = options.filename
                        .substr(0, MAX_FILENAME_LENGTH - 3) + '...';
                }

                options.add.hide();
                options.adding.html(interpolate(gettext('Uploading "%s"...'),
                                                [options.filename]))
                              .show();
                options.loading.removeClass('empty');
                options.progress.show();
                return options;
            },
            onComplete: function(theInput, iframe, options) {
                var iframeJSON = $.parseJSON(iframe[0].contentWindow
                                                 .document.body.innerHTML),
                    upStatus = iframeJSON.status,
                    upFile = iframeJSON.files[0],
                    thumbnail;

                if (upStatus == 'success') {
                    thumbnail = options.progress.clone();
                    options.progress.hide();
                    thumbnail
                        .attr({alt: upFile.name, title: upFile.name,
                               width: upFile.width, height: upFile.height,
                               src: upFile.thumbnail_url})
                        .removeClass('upload-progress')
                        .wrap('<a href="' + upFile.url + '"></a>')
                        .parent()
                        .addClass('attachment')
                        .insertBefore(options.progress);
                } else {
                    options.progress.html(interpolate(
                        gettext('Error uploading "%s"'), [options.filename]));
                }

                options.adding.hide();
                options.add.show();
            }
        });
    });
});


/**
 * Takes a file input, wraps it in a form, creates an iframe and posts the form
 * to that iframe on submit.
 * Allows for the following options:
 * beforeSubmit: function called on submit, before the form data is POSTed.
 * onComplete: function called when iframe has finished loading and the upload
 *             is complete.
 */
jQuery.fn.uploadInput = function (options) {

    // Only works on <input type="file"/>
    if (this[0].nodeName !== 'INPUT' ||
        this.attr('type') !== 'file') {
        return this;
    }

    options = $.extend({
        url: '/upload',
        beforeSubmit: function() {},
        onComplete: function() {}
    }, options);

    var uniqueID = Math.random() * 100000,
        theInput = this,
        parentForm = theInput.closest('form'),
        iframeName = 'upload_' + uniqueID,
        theForm = '<form class="upload-input" action="' +
                    options.url + '" target="' + iframeName +
                    '" method="post" enctype="multipart/form-data"/>',
        iframe = $('<iframe name="' + iframeName +
                   '" style="position:absolute;top:-9999px;" />')
                    .appendTo('body');
    theInput.wrap(theForm);
    theForm = theInput.closest('form');
    // add the csrfmiddlewaretoken to the upload form
    parentForm.find('input[name="csrfmiddlewaretoken"]').clone()
              .appendTo(theForm);

    theInput.change(function() {
        var passJSON = options.beforeSubmit(theInput);

        if (false === passJSON) {
            return false;
        }

        iframe.load(function() {
            options.onComplete(theInput, iframe, passJSON);
        });

        theForm.submit();
    });

    return this;
}
