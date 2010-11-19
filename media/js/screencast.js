/*
 * screencast.js
 * Scripts for Media, such as <video>
 */

(function () {
    var VIDEO_ID_PREFIX = 'video-flash-', id_counter = 0,
        MEDIA_URL = '/media/',  // same value as settings.py
        FLASH_VERSION = '9.0.0',
        params = {allowfullscreen: 'true'},
        flashvars = {
            autoload: 1,
            showtime: 1,
            showvolume: 1
        };
    /*
     * Initializes flash fallback for a video object.
     */
    function initVideoFallback($video) {
        if ($video[0].tagName !== 'VIDEO') return;

        var formats = {ogg: false, webm: false}, i,
            width = Number($video.attr('width')),
            height = Number($video.attr('height')),
            // Build a unique ID for the object container
            unique_id = VIDEO_ID_PREFIX + id_counter,
            flash_file,
            $video_modal = $video.closest('.video').find('.video-modal'),
            $video_modal_trigger = $video.closest('.video')
                .find('.video-modal-trigger');
        id_counter++;

        $video.attr('id', unique_id);

        // Check supported formats
        $('source', $video).each(function checkSourceFormats() {
            for (i in formats) {
                if ($(this).attr('type').indexOf(i) > -1) {
                    formats[i] = true;
                }
            }
        });

        if ($video_modal.length > 0) {
            $video_modal_trigger.initClickModal({
                    modal: $video_modal,
                    overlay_close: true,
                    escape_close: true
                });
        }

        if (Modernizr.video &&  // can the browser play video?
            // do we have a webm it can play?
            (formats.webm && Modernizr.video.webm) ||
            // or do we have an ogg it can play?
            (formats.ogg && Modernizr.video.ogg)) {
            // good news everyone! No need to fall back!
            return false;
        }

        // Get the video fallback URL
        flash_file = $video.attr('data-fallback');
        if (flash_file.substr(-4) === '.swf') {
            swfobject.embedSWF(
                flash_file, unique_id, width, height, FLASH_VERSION,
                MEDIA_URL + '/media/swf/expressInstall.swf', flashvars, params);
        } else if (flash_file) {
            flashvars.flv = flash_file;
            swfobject.embedSWF(
                MEDIA_URL + 'swf/screencast.swf', unique_id, width, height,
                FLASH_VERSION, MEDIA_URL + '/media/swf/expressInstall.swf',
                flashvars, params);
        } else {
            $video.hide();
        }
    };

    /*
     * Checks if fallback is necessary and sets objects in place
     * for the SWF player
     */
    function initFallbackSupport() {
        $('div.video video').each(function initializeVideo(i) {
            initVideoFallback($(this));
        });
    };

    $(document).ready(function () {
        initFallbackSupport();
    });

    // add this to window.k
    k.initVideo = initFallbackSupport;
}());
