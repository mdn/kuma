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
        var $form = $(this).closest('form');
        $(this).wrapDeleteInput({
            error_title_del: UPLOAD.error_title_del,
            error_login: UPLOAD.error_login,
            onComplete: function() {
                $form.trigger('ajaxComplete');
            }
        });
    });

    // Upload a file on input value change
    $('div.attachments-upload input[type="file"]').each(function() {
        var $form = $(this).closest('form');
        $form.removeAttr('enctype');
        $(this).ajaxSubmitInput({
            url: $(this).closest('.attachments-upload').data('post-url'),
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
                    upFile = iframeJSON.file;
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
                        error_login: UPLOAD.error_login,
                        onComplete: function() {
                            $form.trigger('ajaxComplete');
                        }
                    });
                } else {
                    dialogSet(iframeJSON.message, UPLOAD.error_title_up);
                }

                $options.adding.hide();
                $options.add.show();

                $form.trigger('ajaxComplete');
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
