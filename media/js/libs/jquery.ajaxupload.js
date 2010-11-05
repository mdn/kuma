/**
 * JavaScript library written for Kitsune by Mozilla.
 * License: MPL
 * License URL: http://www.mozilla.org/MPL/
 *
 * Contains two jQuery functions: wrapDeleteInput and ajaxSubmitInput.
 * These are helpers for posting data from a <form> to an <iframe> in Django.
 * They use and require the csrfmiddlewaretoken (you may remove those lines
 * if you want to avoid that).
 */


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
