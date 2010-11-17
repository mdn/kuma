$(document).ready(function () {
    var CONSTANTS = {
            maxFilenameLength: 80  // truncated on display, if longer
        },
        $uploadModal = $('#gallery-upload-modal'),
        $radios = $('input[type="radio"]', $uploadModal),
        $forms = $('#gallery-upload-image, #gallery-upload-video'),
        current = 0;

    CONSTANTS.messages = [
            {'invalid': gettext('Invalid image. Please select a valid image file.'),
             'cancelled': gettext('Upload cancelled. Please select an image file.'),
             'del': gettext('Delete this image')},
            {'invalid': gettext('Invalid video. Please select a valid video file (%s).'),
             'cancelled': gettext('Upload cancelled. Please select a video file (%s).'),
             'del': gettext('Delete %s file')}];

    jQuery.fn.makeCancelUpload = function (options) {
        var $this = this;
        if (!$this.is('input')) {
            return $this;
        }

        // drafts: delete, regular cancel: just close the modal
        $this.wrap('<form class="inline" method="POST" action="' +
                     $(this).attr('data-action') + '"/>')
               .closest('form')
               .append($('input[name="csrfmiddlewaretoken"]').first()
                       .clone());

        // now bind to the click event
        $this.click(function (ev) {
            var $this = $(this);
            if ($this.hasClass('draft') ||
                $this.closest('.upload-form').hasClass('uploading')) {

                // Delete draft asynchronously
                var $cancelForm = $this.closest('form'),
                    $uploadForm = $this.closest('.upload-form');
                $.ajax({
                    url: $cancelForm.attr('action'),
                    type: 'POST',
                    data: $cancelForm.serialize(),
                    dataType: 'json'
                    // Ignore the response, nothing to do.
                });

                // Clean up
                $this.removeClass('draft');
                $uploadForm.removeClass('uploading')
                    .find('div.row-right.preview').html('');
                $('#gallery-upload-type').show();
                $uploadForm.find('.upload-media').show();
                $uploadForm.find('.progress, .preview, .metadata').hide();
            }
            return false;
        });

        return $this;
    };

    init();

    /**
     * Shows and hides media fields depending on which have been uploaded to
     * the preview area.
     */
    function showEmptyMediaFields($form) {
        $('.upload-media', $form).each(function () {
            // if there's a preview with the class of the input name
            if ($('.image-preview,.video-preview', $form).filter('.' +
                $(this).find('input').attr('name')).length) {
                $(this).hide();
            } else {
                $(this).show();
            }
        });
        if ($('.upload-media:visible', $form).length === 1) {
            // only label is left, hide it too
            $('label.upload-media', $form).hide();
        }
    }

    /**
     * Hides and shows form fields depending on the received media types.
     * toShow and toHide are the corresponding integer indices in
     * MEDIA_TYPES.
     */
    $radios.click(function changeMediaType() {
        // TODO: change this to use CSS classes + transitions instead of fades
        current = $radios.index($(this));
        var $toShow = $forms.eq(current),
            $toHide = $forms.not($toShow),
            $preview = $('.preview', $toShow),
            $toShowMetadata = $('.metadata', $toShow);
        $('.progress', $toShow).hide();
        if ($toShowMetadata.length === 0) {
            $('.metadata', $uploadModal).insertBefore(
                $('.upload-action', $toShow));
        }
        if ($preview.find('.image-preview,.video-preview').length > 0) {
            showEmptyMediaFields($toShow);
            $preview.show();
            // move metadata from one form to another
            $('.metadata', $toShow).show();
        } else {
            $preview.hide();
            $('.upload-media', $toShow).show();
            $('.metadata', $toShow).hide();
        }
        $toHide.fadeOut('fast', function toggleForms() {
            $toHide.hide();
            $toShow.fadeIn('fast');
        });
    });

    // this makes it play nice with form history and page reloads
    $radios.filter(':checked').click();

    // Upload a file on input value change
    $('input[type="file"]', $uploadModal).each(function() {
        var $form = $(this).closest('.upload-form'),
            type = 'image';
        $form.removeAttr('enctype');
        $(this).ajaxSubmitInput({
            url: $(this).closest('.upload-form').attr('data-post-url'),
            beforeSubmit: function($input) {
                var upName = $input.attr('name'),
                    $options = {
                        form: $form,
                        add: $input.closest('.upload-media'),
                        metadata: $('.metadata', $form),
                        filename: $input.val().split(/[\/\\]/).pop(),
                        progress: $('.progress', $form).filter('.' + upName)
                    };
                $form.find('input[type="submit"]').not('[name="cancel"]')
                    .attr('disabled', 'disabled');
                $options.remaining = $('.upload-media:visible', $form);
                // if there are other inputs remaining to upload
                // don't hide the Video label
                if ($options.remaining.length > 2 && upName !== 'thumbnail') {
                    $options.remaining = $();  // empty
                } else if (upName === 'thumbnail') {
                    $options.remaining = $('.upload-media.thumbnail', $form)
                        .not($options.add);
                } else {
                    $options.remaining = $options.remaining.not($options.add);
                }
                $options.adding = $options.progress.find('span');
                $options.add.find('.invalid').removeClass('invalid');

                // truncate filename
                if ($options.filename.length > CONSTANTS.maxFilenameLength) {
                    $options.filename = $options.filename
                        .substr(0, CONSTANTS.maxFilenameLength - 3) + '...';
                }

                $options.progress.find('a').click(function cancelUpload() {
                    $('iframe[name="' + $input.closest('form').attr('target') +
                      '"]')[0].src = null;
                    var message = CONSTANTS.messages[current].cancelled;
                    message = interpolate(message, [upName]);
                    reUploadWithMessage($options, message);
                    $options.remaining.fadeIn('fast');
                    return false;
                });
                $options.adding.html(interpolate(gettext('Uploading "%s"...'),
                                                 [$options.filename]));
                $('#gallery-upload-type').fadeOut('fast');
                $options.remaining.fadeOut('fast');
                $options.add.fadeOut('fast', function editMetadata() {
                    if ($options.add.find('.invalid').length === 0) {
                        $options.progress.fadeIn('fast');
                        $options.metadata.fadeIn('fast');
                    }
                }).addClass('uploading');
                $form.addClass('uploading');

                return $options;
            },
            onComplete: function($input, iframeContent, $options) {
                $input.closest('form')[0].reset();
                $form.find('input[type="submit"]').attr('disabled', '');
                if (!iframeContent) {
                    return;
                }
                var iframeJSON;
                try {
                    iframeJSON = $.parseJSON(iframeContent);
                } catch(err) {
                    if (err.substr(0, 12)  === 'Invalid JSON') {
                        alert(err);
                        return false;
                    }
                }

                var upName = $input.attr('name'),
                    upStatus = iframeJSON.status, upFile, $thumbnail,
                    $cancel_btn = $('.upload-action input[name="cancel"]',
                                    $options.form),
                    message, message_index,
                    $appendCancelTo = $('.row-right.preview', $options.form);

                message_index = current;
                if (upName === 'thumbnail') {
                    // treat thumbnails like images
                    message_index = 0;  // image index
                }
                if (upStatus !== 'success') {
                    message = CONSTANTS.messages[message_index].invalid;
                    message = interpolate(message, [upName]);
                    reUploadWithMessage($options, message, true);
                    return false;
                }
                upFile = iframeJSON.file;

                // Make cancel buttons delete the draft
                $cancel_btn.addClass('draft');
                message = CONSTANTS.messages[message_index].del;
                if (upName === 'file') {
                    // create thumbnail
                    $thumbnail = $('<img/>')
                        .attr({alt: upFile.name, title: upFile.name,
                               width: upFile.width, height: upFile.height,
                               src: upFile.thumbnail_url})
                        .wrap('<div class="image-preview"/>').closest('div')
                        .appendTo($('.row-right.preview', $options.form));
                } else if (upName === 'thumbnail') {
                    $('.row-right.thumbnail', $options.form)
                        .children().hide();
                    $thumbnail = $('<img/>')
                        .attr({alt: upFile.name, title: upFile.name,
                               width: upFile.width, height: upFile.height,
                               src: upFile.thumbnail_url})
                        .wrap('<div class="image-preview"/>').closest('div')
                        .appendTo($('.row-right.uploading.thumbnail',
                                    $options.form));
                    $('.row-right.thumbnail,.row-left.thumbnail',
                      $options.form).show();
                    $appendCancelTo = $('.row-right.thumbnail', $options.form);
                } else {
                    $appendCancelTo = $('<li class="video-preview"/>');
                    $appendCancelTo.html($options.filename)
                        .appendTo($('.row-right.preview ul', $options.form));
                    message = interpolate(message, [upName]);
                }
                $cancel_btn.clone().val(message)
                           .attr('data-action',
                                 $cancel_btn.attr('data-action') +
                                 '?field=' + upName.toLowerCase())
                           .appendTo($appendCancelTo)
                           .makeCancelUpload();
                $options.progress.fadeOut('fast', function () {
                    if (!$options.progress.hasClass('thumbnail')) {
                        $('.preview', $options.form).fadeIn('fast');
                    }
                });
            }
        });
    }); // end ajax upload gallery code


    function reUploadWithMessage($options, message, invalid) {
        var $msgContainer = $options.add.filter('.row-right').find('label'),
            in_progress = $('.upload-media.uploading', $options.form).length,
            $progress = $options.progress;
        $msgContainer.html(message);
        $options.form.find('input[type="submit"]').attr('disabled', '');
        if (invalid) {
            $msgContainer.addClass('invalid');
        } else {
            $msgContainer.removeClass('invalid');
        }
        if (in_progress <= 1 && !$options.add.hasClass('thumbnail')) {
            $options.metadata.fadeOut('fast');
        } else if ($options.add.hasClass('thumbnail')) {
            in_progress = 2;
        } else {  // if (in_progress > 2) {
            $progress = $progress.not('label');
        }
        $progress.fadeOut('fast', function chooseAgain() {
            $options.add.fadeIn('fast').removeClass('uploading');
            $options.form.removeClass('uploading');
            $('label.upload-media', $options.form).fadeIn('fast');
            // check if other uploads are still in progress before showing this
            if (in_progress <= 1) {
                $('#gallery-upload-type').fadeIn('fast');
            }
        });
    }

    function init() {
        // if there are drafts, open the modal
        if ($forms.hasClass('draft')) {
            $radios.eq($forms.index($forms.filter('.draft'))).click();
            $('.btn-upload').click();
        }
        // auto-open the modal window when drafts are present
        $uploadModal.find('input[name="cancel"]').each(function () {
            $(this).makeCancelUpload();
        });
        // Closing the modal with top-right X cancels upload drafts
        $uploadModal.delegate('a.close', 'click', function(e) {
            $uploadModal.find('input.draft[name="cancel"]:last').click();
        });
    }
});

