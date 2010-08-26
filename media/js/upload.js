$(document).ready(function () {
    var UPLOAD = {
            max_filename_length: 80,  // max filename length in characters
            error_title_up: gettext('Error uploading image'),
            error_title_del: gettext('Error deleting image'),
            error_login: gettext('Please check you are logged in, and try again.'),
            $dialog: $('#upload_dialog')
        };
    if (UPLOAD.$dialog.length <= 0) {
        UPLOAD.$dialog = $('<div id="upload-dialog"></div>')
                    .appendTo('body');
    }
    UPLOAD.$dialog.dialog({autoOpen: false});

    function dialogSet(inner, title, stayClosed) {
        UPLOAD.$dialog.html(inner);
        UPLOAD.$dialog.dialog('option', 'title', title);
        if (stayClosed === true) {
            return;
        }
        UPLOAD.$dialog.dialog('open');
    }

    $('input.delete', 'div.attachments-list').each(function () {
        $(this).wrapDeleteInput({
            error_title_del: UPLOAD.error_title_del,
            error_login: UPLOAD.error_login
        });
    });

    // Upload a file on input value change
    $('div.attachments-upload input[type="file"]').each(function() {
        $(this).closest('form').removeAttr('enctype');
        $(this).ajaxSubmitInput({
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
                if ($options.filename.length > UPLOAD.max_filename_length) {
                    $options.filename = $options.filename
                        .substr(0, UPLOAD.max_filename_length - 3) + '...';
                }

                $options.add.hide();
                $options.adding.html(interpolate(gettext('Uploading "%s"...'),
                                                [$options.filename]))
                              .show();
                $options.loading.removeClass('empty');
                $options.progress.addClass('show');
                return $options;
            },
            onComplete: function($input, iframeContent, $options) {
                $input.closest('form')[0].reset();
                if (!iframeContent) {
                    return;
                }
                var iframeJSON;
                try {
                    iframeJSON = $.parseJSON(iframeContent);
                } catch(err) {
                    if (err.substr(0, 12)  === 'Invalid JSON') {
                        dialogSet(UPLOAD.error_login, UPLOAD.error_title_up);
                    }
                }
                var upStatus = iframeJSON.status, upFile, $thumbnail;

                $options.progress.removeClass('show');
                if (upStatus == 'success') {
                    upFile = iframeJSON.files[0];
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
                    $thumbnail.prepend(
                        '<input type="submit" class="delete" data-url="' +
                        upFile.delete_url + '" value="&#x2716;"/>');
                    $thumbnail.children().first().wrapDeleteInput({
                        error_title_del: UPLOAD.error_title_del,
                        error_login: UPLOAD.error_login
                    });
                } else {
                    dialogSet(iframeJSON.message, UPLOAD.error_title_up);
                }

                $options.adding.hide();
                $options.add.show();
            }
        });
    });

    // Workaround to IE6's lack of div:hover support
    if($.browser.msie && $.browser.version=="6.0") {
        $('div.attachments-upload').delegate('div.attachment', 'hover',
            function(ev) {
                if (ev.type == 'mouseover' || ev.type == 'mouseenter') {
                    $(this).addClass('hover');
                } else {
                    $(this).removeClass('hover');
                }
            });
    }
});


/**
 * Wrap an input in its own form and bind delete handlers.
 *
 * Depends on ajaxSubmitInput, which it binds to the click event on the delete
 * <input>.
 * Optionally accepts an error message for invalid JSON and a title for
 * the error message dialog.
 *
 * Uses jQueryUI for the dialog.
 */
jQuery.fn.wrapDeleteInput = function (options) {
    // Only works on <input/>
    if (!this.is('input')) {
        return this;
    }

    options = $.extend({
        error_title_del: 'Error deleting',
        error_json: 'Please check you are logged in, and try again.'
    }, options);

    var $that = this,
        $attachment = $that.closest('.attachment'),
        $image = $attachment.find('.image');

    $that.ajaxSubmitInput({
        url: $that.attr('data-url'),
        inputEvent: 'click',
        beforeSubmit: function($input) {
            var $overlay = $input.closest('.overlay', $attachment);
            if ($overlay.length <= 0) {
                $overlay = $('<div class="overlay"></div>')
                               .appendTo($attachment);
            }
            $overlay.show();
            $image.fadeTo(500, 0.5);
        },
        onComplete: function($input, iframeContent, $options) {
            if (!iframeContent) {
                $image.css('opacity', 1);
                return;
            }
            var iframeJSON;
            try {
                iframeJSON = $.parseJSON(iframeContent);
            } catch(err) {
                if (err.substr(0, 12)  === 'Invalid JSON') {
                    dialogSet(options.error_json, options.error_title_del);
                    $image.css('opacity', 1);
                    return;
                }
            }
            if (iframeJSON.status !== 'success') {
                dialogSet(iframeJSON.message, options.error_title_del);
                $image.css('opacity', 1);
                return;
            }
            $attachment.remove();
        }
    });

    return this;
};


/**
 * Takes a file input, wraps it in a form, creates an iframe and posts the form
 * to that iframe on submit.
 * Allows for the following options:
 * accept: list of MIME types to accept. See the HTML accept attribute.
 * beforeSubmit: function called on submit, before the form data is POSTed.
 * onComplete: function called when iframe has finished loading and the upload
 *             is complete.
 */
jQuery.fn.ajaxSubmitInput = function (options) {
    // Only works on <input/>
    if (!this.is('input')) {
        return this;
    }

    options = $.extend({
        url: '/upload',
        accept: false,
        inputEvent: 'change',
        beforeSubmit: function() {},
        onComplete: function() {}
    }, options);

    var uniqueID = Math.random() * 100000,
        $input = this,
        $parentForm = $input.closest('form'),
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
    $('input[name="csrfmiddlewaretoken"]').first().clone().appendTo($form);

    $iframe.load(function() {
        var iframeContent = $iframe[0].contentWindow.document.body.innerHTML;
        options.onComplete($input, iframeContent, passJSON);
    });

    $input.bind(options.inputEvent, function() {
        passJSON = options.beforeSubmit($input);

        if (false === passJSON) {
            return false;
        }

        $form.submit();
    });

    return this;
};
