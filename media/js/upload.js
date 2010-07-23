$(document).ready(function () {
    var MAX_FILENAME_LENGTH = 80;  // max filename length in characters

    // Delete an image
    function deleteImageAttachment() {
        var $that = $(this),
            $attachment = $that.closest('.attachment'),
            $image = $attachment.find('.image'),
            $overlay = $that.closest('.overlay', $attachment);
        $.ajax({
            url: $that.attr('href'),
            dataType: 'json',
            error: function() {
                $image.css('opacity', 1);
            },
            success: function(response) {
                if (response.status === 'success') {
                    $attachment.remove();
                }
            }
        });

        if ($overlay.length <= 0) {
            $overlay = $('<div class="overlay"></div>').appendTo($attachment);
        }
        $overlay.show();

        $image.fadeTo(500, 0.5);

        return false;
    };

    $('div.attachments-upload').delegate('a.delete', 'click',
                                         deleteImageAttachment);
    $('div.ans-attachments a.delete').click(deleteImageAttachment);

    // Upload a file on input value change
    $('div.attachments-upload input[type="file"]').each(function() {
        $(this).closest('form').removeAttr('enctype');
        $(this).uploadInput({
            url: $(this).closest('.attachments-upload').attr('data-post-url'),
            beforeSubmit: function($input) {
                var $divUpload = $input.closest('.attachments-upload'),
                    $options = {
                        progress: $divUpload.find('.upload-progress'),
                        add: $divUpload.find('.add-attachment'),
                        adding: $divUpload.find('.adding-attachment'),
                        loading: $divUpload.find('.uploaded')
                    };

                // truncate filename
                $options.filename = $input.val().split(/[\/\\]/).pop();
                if ($options.filename.length > MAX_FILENAME_LENGTH) {
                    $options.filename = $options.filename
                        .substr(0, MAX_FILENAME_LENGTH - 3) + '...';
                }

                $options.add.hide();
                $options.adding.html(interpolate(gettext('Uploading "%s"...'),
                                                [$options.filename]))
                              .show();
                $options.loading.removeClass('empty');
                $options.progress.addClass('show');
                return $options;
            },
            onComplete: function($input, $iframe, $options) {
                var iframeContent = $iframe[0].contentWindow
                                                 .document.body.innerHTML;
                $input.closest('form')[0].reset();
                if (!iframeContent) {
                    return;
                }
                var iframeJSON = $.parseJSON(iframeContent),
                    upStatus = iframeJSON.status, upFile,
                    $thumbnail;

                if (upStatus == 'success') {
                    upFile = iframeJSON.files[0];
                    $options.progress.removeClass('show');
                    $thumbnail = $('<img/>')
                        .attr({alt: upFile.name, title: upFile.name,
                               width: upFile.width, height: upFile.height,
                               src: upFile.thumbnail_url})
                        .removeClass('upload-progress')
                        .wrap('<a class="image" href="' + upFile.url + '"></a>')
                        .closest('a')
                        .wrap('<div class="attachment"></div>')
                        .closest('div')
                        .addClass('attachment')
                        .insertBefore($options.progress);
                    $thumbnail.prepend('<a class="delete" href="' +
                                      upFile.delete_url + '">✖</a>');
                } else {
                    $options.adding.html(interpolate(
                        gettext('Error uploading "%s"'), [$options.filename]));
                }

                $options.adding.hide();
                $options.add.show();
            }
        });
    });
});


/**
 * Takes a file input, wraps it in a form, creates an iframe and posts the form
 * to that iframe on submit.
 * Allows for the following options:
 * accept: list of MIME types to accept. See the HTML accept attribute.
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
        accept: false,
        beforeSubmit: function() {},
        onComplete: function() {}
    }, options);

    var uniqueID = Math.random() * 100000,
        $input = this,
        parentForm = $input.closest('form'),
        iframeName = 'upload_' + uniqueID,
        $form = '<form class="upload-input" action="' +
                options.url + '" target="' + iframeName +
                '" method="post" enctype="multipart/form-data"/>',
        $iframe = $('<iframe name="' + iframeName +
                   '" style="position:absolute;top:-9999px;" />')
                   //'" style="position:fixed;top:0px;width:500px;height:350px" />')
                    .appendTo('body'),
        passJSON;

    if (options.accept) {
        $input.attr('accept', options.accept);
    }

    $input.wrap($form);
    $form = $input.closest('form');
    // add the csrfmiddlewaretoken to the upload form
    parentForm.find('input[name="csrfmiddlewaretoken"]').clone()
              .appendTo($form);

    $iframe.load(function() {
        options.onComplete($input, $iframe, passJSON);
    });

    $input.change(function() {
        passJSON = options.beforeSubmit($input);

        if (false === passJSON) {
            return false;
        }

        $form.submit();
    });

    return this;
}
