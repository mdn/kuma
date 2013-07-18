/**
 * Various tools for the HTML5 video element.
 *
 * Meant to be used with CSS in /media/css/video-player.css.
 *
 * Video lightbox is documented below in Mozilla.VideoPlayer.prepare_video
 *
 * This file contains Flash-detection routines adapted from SWFObject and
 * originally licensed under the MIT license.
 *
 * See http://blog.deconcept.com/flashobject/
 *
 * @copyright 2009-2010 Mozilla Corporation
 * @author    Michael Gauthier <mike@silverorange.com>
 * @author    Austin King <ozten@mozilla.com> - Moved to MDN, ported to jQuery
 */

/*global window: false, document: false, navigator: false, self: false */
/*global HTMLMediaElement: false, ActiveXObject: false, require: false */
/*global $: false, */
/*jslint plusplus: false, nomen: false */

var Mozilla;
if (typeof Mozilla === 'undefined') {
    Mozilla = {};
}

Mozilla.VideoControl = function () {};
Mozilla.VideoControl.controls = [];

/**
 * Initializes video controls and video scalers on this page after the 
 * document has been loaded
 */
$(document).ready(function ()
{
    $('.mozilla-video-control').each(function (i, video) {
        Mozilla.VideoControl.controls.push(new Mozilla.VideoControl(video));
    });
    $('.mozilla-video-scaler').each(function (i, video) {
        Mozilla.VideoScaler.scalers.push(new Mozilla.VideoScaler(video));
    });
});

/**
 * Scales a video to full size then the video's click-to-play button
 * is clicked
 *
 * If the HTML5 video element is supported, the following markup will
 * automatically get this behaviour when the page initializes:
 * <code>
 * &lt;div class="mozilla-video-scaler"&gt;
 *     &lt;div class="mozilla-video-control"&gt;
 *         &lt;video ... /&gt;
 *     &lt;/div&gt;
 * &lt;/div&gt;
 * </code>
 *
 * @param DOMElement|String container
 */
Mozilla.VideoScaler = function (container) {};

Mozilla.VideoScaler.scalers = [];
Mozilla.VideoScaler.close_text = 'Close';

/**
 * Popup player using HTML5 video element with flash fallback
 *
 * @param String  id
 * @param Array   sources
 * @param String  flv url
 * @param Booelan autoplay
 */
Mozilla.VideoPlayer = function (id, sources, flv_url, autoplay)
{
    var that = this;
    this.id       = id;
    this.flv_url  = flv_url;
    this.sources  = sources;
    this.opened   = false;

    if (arguments.length > 3) {
        this.autoplay = autoplay;
    } else {
        this.autoplay = true;
    }

    $(document).ready(function () {
        that.init();
    });
};

Mozilla.VideoPlayer.height = '360';
Mozilla.VideoPlayer.width  = '640';

Mozilla.VideoPlayer.close_text = $('#video-player-close').text();
Mozilla.VideoPlayer.fallback_text = $('#video-player-fallback').html();

Mozilla.VideoPlayer.prototype.init = function ()
{
    var body, video_link, preview_link, that;
    that = this;
    this.overlay = document.createElement('div');
    this.overlay.className = 'mozilla-video-player-overlay';
    this.overlay.style.display = 'none';

    this.video_container = document.createElement('div');
    this.video_container.className = 'mozilla-video-player-window';
    this.video_container.style.display = 'none';

    // add overlay and preview image to document
    body = document.getElementsByTagName('body')[0];
    body.appendChild(this.overlay);
    body.appendChild(this.video_container);

    // set video link event handler
    video_link = document.getElementById(this.id);

    $('#' + this.id + ',' + '#' + this.id + '-preview').click(function (e) {
        e.preventDefault();
        that.open();
    });
};

Mozilla.VideoPlayer.prototype.clearVideoPlayer = function ()
{
    var videos, i;
    $(this.video_container).unbind('click');

    // workaround for FF Bug #533840, manually pause all videos
    videos = this.video_container.getElementsByTagName('video');
    for (i = 0; i < videos.length; i++) {
        videos[i].pause();
    }

    // remove all elements
    while (this.video_container.childNodes.length > 0) {
        this.video_container.removeChild(this.video_container.firstChild);
    }
};

Mozilla.VideoPlayer.prototype.drawVideoPlayer = function ()
{
    var close_div, close_link, video_div, content, i, that, titles, download;
    this.clearVideoPlayer();

    close_div = document.createElement('div');
    close_div.className = 'mozilla-video-player-close';

    close_link = document.createElement('a');
    close_link.href = '#';

    that = this;
    $(close_link).click(function (e) {
        e.preventDefault();
        that.close();
    });
    close_link.appendChild(document.createTextNode(
        Mozilla.VideoPlayer.close_text));
    
    close_div.appendChild(close_link);
    this.video_container.appendChild(close_div);

    video_div = document.createElement('div');
    video_div.className = 'mozilla-video-player-content';

    // get content for player
    if (typeof HTMLMediaElement !== 'undefined') {
        content = this.getVideoPlayerContent();
    } else if (Mozilla.VideoPlayer.flash_verison.isValid([7, 0, 0])) {
        content = this.getFlashPlayerContent();
    } else {
        content = this.getFallbackContent();
    }

    titles = {
        'video/webm': 'WebM',
        'video/ogg': 'Ogg&nbsp;Theora',
        'video/mp4': 'MPEG-4'
    };
    download = $('#video-player-download-link').text();
    // add download links
    content += '<div class="video-download-links">' + download + ' <ul>';
    for (i = 0; i < this.sources.length; i++) {
        content +=
            '<li><a href="' + this.sources[i].url + '">' +
            titles[this.sources[i].type] + '</a></li>';
    }
    content += '</ul></div>';

    this.video_container.appendChild(video_div);
    video_div.innerHTML = content;
};

Mozilla.VideoPlayer.prototype.getVideoPlayerContent = function ()
{
    var content =
            '<video width="' + Mozilla.VideoPlayer.width + '" ' +
            'height="' + Mozilla.VideoPlayer.height + '" ' + 
            'controls="controls"', i;
    if (this.autoplay) {
        content += ' autoplay="autoplay"';
    }

    content += '>';


    for (i = 0; i < this.sources.length; i++) {
        if (!this.sources[i].type) {
            continue; // must have MIME type
        }
        content +=
            '<source src="' + this.sources[i].url + '" ' +
            'type="' + this.sources[i].type + '"/>';
    }

    content += '</video>';

    return content;
};

Mozilla.VideoPlayer.prototype.getFlashPlayerContent = function ()
{
    var url = '/media/img/tignish/video/playerWithControls.swf?flv=' + 
              this.flv_url,
        content;
    if (this.autoplay) {
        url += '&autoplay=true';
    } else {
        url += '&autoplay=false';
    }
    content =
        '<object type="application/x-shockwave-flash" style="' +
        'width: ' + Mozilla.VideoPlayer.width + 'px; ' + 
        'height: ' + Mozilla.VideoPlayer.height + 'px;" ' +
        'wmode="transparent" data="' + url + '">' + 
        '<param name="movie" value="' + url + '" />' + 
        '<param name="wmode" value="transparent" />' +
        '</object>';

    return content;
};

Mozilla.VideoPlayer.prototype.getFallbackContent = function ()
{
    var content =
        '<div class="mozilla-video-player-no-flash">' +
        Mozilla.VideoPlayer.fallback_text +
        '</div>';
    return content;
};

Mozilla.VideoPlayer.prototype.open = function ()
{
    // hide the language form because its select element won't render
    // correctly in IE6
    var hide_form = document.getElementById('lang_form');

    if (hide_form) {
        hide_form.style.display = 'none';
    }

    this.overlay.style.height = $(document).height() + 'px';
    this.overlay.style.display = 'block';

    this.video_container.style.display = 'block';

    this.drawVideoPlayer();

    this.video_container.style.top = ($(window).scrollTop() + 
        ($(window).height() - 570) / 2) + 'px';
    this.opened = true;
};

Mozilla.VideoPlayer.prototype.close = function ()
{
    this.overlay.style.display = 'none';
    this.video_container.style.display = 'none';

    // clear the video content so IE will stop playing the audio
    this.clearVideoPlayer();

    // if language form was hidden, show it again
    var hide_form = document.getElementById('lang_form');
    if (hide_form) {
        hide_form.style.display = 'block';
    }

    this.opened = false;
};


Mozilla.VideoPlayer.getFlashVersion = function ()
{
    var version, x, axo, flash_version,
        major_version = 0;
    version = new Mozilla.FlashVersion([0, 0, 0]);
    if (navigator.plugins && navigator.mimeTypes.length) {
        x = navigator.plugins['Shockwave Flash'];
        if (x && x.description) {
            // strip text to get version number only
            version = x.description.replace(/([a-zA-Z]|\s)+/, '');

            // convert revisions and beta to dots
            version = version.replace(/(\s+r|\s+b[0-9]+)/, '.');

            // get version
            version = new Mozilla.FlashVersion(version.split('.'));
        }
    } else {
        if (navigator.userAgent && 
            navigator.userAgent.indexOf('Windows CE') >= 0) {

            axo = true;
            flash_version = 3;
            while (axo) {                
                // look for greatest installed version starting at 4
                try {
                    major_version++;
                    axo = new ActiveXObject('ShockwaveFlash.ShockwaveFlash.' + 
                          major_version);
                    version = new Mozilla.FlashVersion([major_version, 0, 0]);
                } catch (e1) {
                    axo = null;
                }
            }
        } else {
            try {
                axo = new ActiveXObject('ShockwaveFlash.ShockwaveFlash.7');
            } catch (e2) {
                try {
                    axo = new ActiveXObject('ShockwaveFlash.ShockwaveFlash.6');
                    version = new Mozilla.FlashVersion([6, 0, 21]);
                    axo.AllowScriptAccess = 'always';
                } catch (e3) {
                    if (version.major === 6) {
                        return version;
                    }
                }
                try {
                    axo = new ActiveXObject('ShockwaveFlash.ShockwaveFlash');
                } catch (e4) {}
            }
            if (axo !== null) {
                try {
                    version = new Mozilla.FlashVersion(
                        axo.GetVariable('$version').split(' ')[1].split(','));
                } catch (e4) {}
            }
        }
    }
    return version;
};

Mozilla.FlashVersion = function (version)
{
    this.major = version[0] !== null ? parseInt(version[0], 10) : 0;
    this.minor = version[1] !== null ? parseInt(version[1], 10) : 0;
    this.rev   = version[2] !== null ? parseInt(version[2], 10) : 0;
};

Mozilla.FlashVersion.prototype.isValid = function (version)
{
    if (version instanceof Array) {
        version = new Mozilla.FlashVersion(version);
    }

    if (this.major < version.major) {
        return false;
    }
    if (this.major > version.major) {
        return true;
    }
    if (this.minor < version.minor) {
        return false;
    }
    if (this.minor > version.minor) {
        return true;
    }
    if (this.rev < version.rev) {
        return false;
    }
    return true;
}; 

Mozilla.VideoPlayer.flash_verison = Mozilla.VideoPlayer.getFlashVersion();

/**
 * jQuery compatible wrapper for setting up each
 * video thumbnail.
 * 
 * The CSS class 'video_thumbnail' should be added to
 * any anchor tags which contain an image which when clicked
 * should launch the video player. Formats:
 * The anchor tag *must* have an id that matches this 
 * layout on the video.mozilla.org website
 * http://video.mozilla.org/serv/mdn/${id}/${id}.webm
 * http://video.mozilla.org/serv/mdn/${id}/${id}.ogv
 * http://video.mozilla.org/serv/mdn/${id}/${id}.mp4
 * 
 * @todo The flv flash fallbacks don't seem to work Bug#606355
 * 
 * @param Integer i The counter of which video
 * @param Element thumb The HTML Anchor tag
 */
Mozilla.VideoPlayer.prepare_video = function (i, thumb) {
    var cdn = 'http://videos-cdn.mozilla.net/serv/mdn/',
        id = $(thumb).attr('id'), 
        video_path, video_files, _unused;
    
    video_path = id + '/' + id;
    video_files = [{url: cdn + video_path + '.webm', type: 'video/webm'},
                   {url: cdn + video_path + '.ogv',  type: 'video/ogg'},
                   {url: cdn + video_path + '.mp4',  type: 'video/mp4'}];
    _unused = new Mozilla.VideoPlayer(id, video_files, 
                                      'serv/mdn/' + video_path + '.mp4');
};

$(document).ready(function () {
    var surveyId = 'survey201009',
        video_thumbnails, lightBox, _overlay, positionFixed, 
        height, scrollTop, _link,
    /**
     * From http://yura.thinkweb2.com/cft/
     */
    isPositionFixedSupported = function ()
    {
        var isSupported = false, el, root;

        if (document.createElement) {
            el = document.createElement('div');
            if (el && el.style) {
                el.style.position = 'fixed';
                el.style.top = '10px';
                root = document.body;
                if (root && root.appendChild && root.removeChild) {
                    root.appendChild(el);
                    isSupported = (el.offsetTop === 10);
                    root.removeChild(el);
                }
            }
        }
        return isSupported;
    },
    updatePosition = function (link) {
        var height = $(window).height(),
            scrollTop = $(window).scrollTop();
        link.css('top', (scrollTop + height - 62) + 'px');
    };

    video_thumbnails = $('.video_thumbnail');
    if (video_thumbnails.length > 0) {
        video_thumbnails.each(Mozilla.VideoPlayer.prepare_video);    

        
    
        positionFixed = isPositionFixedSupported();
        height = Math.max($(document).height(), $(window).height());

        _link = $('<div id="' + surveyId + '_image">')
            .css('display', 'none')
            .css('position', 'fixed')
            .css('bottom', '-79px')
            .css('right', '-62px')
            .css('width', '79px')
            .css('height', '62px')
            .css('zIndex', '999')
            .appendTo($('body'));
    
        if (!positionFixed) {
            height = $(window).height();
            scrollTop = $(window).scrollTop();

            _link.css('position', 'absolute')
                 .css('top', height + scrollTop);

            $(window).scroll(function () {
                updatePosition(_link);
            });
        }

        _overlay = $('<div id="' + surveyId + '_overlay">')
            .css('display', 'none')
            .css('position', 'absolute')
            .css('background', '#fff')
            .css('opacity', '0.60')
            .css('top', '0')
            .css('left', '0')
            .css('width', '100%')
            .css('height', height + 'px')
            .css('zIndex', '1000')
            .appendTo($('body'));

        lightBox = $('<div id="' + surveyId + '_box">')
            .css('display', 'none')
            .css('background', '#e3e2e0')
            .css('padding', '10px')
            .css('border', '1px solid #777')
            .css('position', 'absolute')
            .css('width', '660px')
            .css('height', '970px')
            .css('top', '80px')
            .css('left', '50%')
            .css('marginLeft', '-350px')
            .css('zIndex', '1001')
            .css('overflow', 'hidden')
            .css('boxShadow', '0 5px 50px rgba(0,0,0,0.8)')
            .css('MozBoxShadow', '0 5px 50px rgba(0,0,0,0.8)')
            .css('WebkitBoxShadow', '0 5px 40px rgba(0,0,0,0.6)')
            .css('borderRadius', '8px')
            .css('MozBorderRadius', '8px')
            .css('WebkitBorderRadius', '8px')
            .appendTo($('body'));

        $('<a href="#close">Close</a>')
            .css('display', 'block')
            .css('float', 'right')
            .css('padding', '8px 48px 20px 20px')
            .css('background', 'url("/media/img/tignish/firefox/video-close.png") no-repeat 100% 0')
            .click(function (e) {
                e.preventDefault();
                lightBox.css('display', 'none');
                _overlay.css('display', 'none');
            })
            .appendTo(lightBox);

        $('<iframe name="' + surveyId + '_iframe" id="' + surveyId + 
          '_iframe" ' + 'frameBorder="0" ' + '></iframe>')
            .css('background', '#ffffff')
            .css('width', '100%')
            .css('height', '100%')
            .css('border', 'none')
            .css('clear', 'right')
            .appendTo(lightBox);
    } // end if
});
/* end from mobile-video.js */