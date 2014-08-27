(function(win, doc, $) {
    'use strict';

    /*
        Togglers within articles (i.e.)
    */
    $('.toggleable').mozTogglers();

    /*
        Toggle for quick links show/hide
    */
    (function() {
        // Set up the quick links for the toggler
        var $quickLinks = $('#quick-links');
        setupTogglers($quickLinks.find('> ul > li, > ol > li'));
        $quickLinks.find('.toggleable').mozTogglers();

        var $columnContainer = $('#wiki-column-container');
        var $quickLinksControl = $('#wiki-controls .quick-links');

        var child = $('#wiki-left').get(0);
        if(child) {
            var parent = child.parentNode;
        }

        // Quick Link toggles
        $('#quick-links-toggle, #show-quick-links').on('click', function(e) {
            e.preventDefault();
            $(child).toggleClass('column-closed');
            $columnContainer.toggleClass('wiki-left-closed');
            $quickLinksControl.toggleClass('hidden');

            if($(child).hasClass('column-closed')) {
                parent.removeChild(child);
            }
            else {
                parent.appendChild(child);
            }

            mdn.analytics.trackEvent({
                category: 'Wiki',
                action: 'Sidebar',
                label: this.id == 'quick-links-toggle' ? 'Hide' : 'Show'
            });

        });
    })();

    /*
        Set up the zone subnav accordion
    */
    $('.subnav').each(function() {
        var $subnav = $(this);
        var $subnavList = $subnav.find(' > ol');
        var minHeightFn = $('.zone-landing-header-preview-base').length ? setMinHeight : noop;

        if(!$subnavList.length) return; // Exit if the subnav isn't set up properly

        // Set the list items as togglers where needed
        setupTogglers($subnavList.find('li'));

        // Make them toggleable!
        $subnavList.find('.toggleable').mozTogglers({
            slideCallback: minHeightFn
        });

        // Try to find the current page in the list, if found, open it
        // Need to keep track of the elements we've found so they aren't found twice
        var used = [];
        var $selected = $subnavList.find('a[href$="' + doc.location.pathname + '"]');
        $selected.each(function() {
            var self = this;
            var $togglers = $(this).parents('.toggleable').find('.toggler');

            $togglers.each(function() {
                if($.contains($(this).parent('li').get(0), self) && used.indexOf(this) === -1) {
                    $(this).trigger('mdn:click');
                    used.push(this);
                }
            });
        }).parent().addClass('current');

        // Mark this is an accordion so the togglers open/close properly
        $subnavList.addClass('accordion');

        function noop(){}
        function setMinHeight() {
            if($('.zone-landing-header-preview-base').css('position') == 'absolute') {
                $('.wiki-main-content').css('min-height', $subnav.height());
            }
        }

        minHeightFn();
    });

    /*
        Set up the "from search" buttons if user came from search
    */
    var fromSearchNav = $('.from-search-navigate');
    if(fromSearchNav.length) {
        var fromSearchList = $('.from-search-toc');
        fromSearchNav.mozMenu({
            submenu: fromSearchList,
            brickOnClick: true,
            onOpen: function(){
                mdn.analytics.trackEvent({
                    category: 'Search doc navigator',
                    action: 'Open on hover',
                });
            },
            onClose: function() {
                mdn.analytics.trackEvent({
                    category: 'Search doc navigator',
                    action: 'Close on blur',
                });
            }
        });
        fromSearchList.find('ol').mozKeyboardNav();
    }

    /*
        Subscribe / unsubscribe to an article
    */
    $('.page-watch a').on('click', function(e) {
        e.preventDefault();

        var $link = $(this);
        if($link.hasClass('disabled')) return;

        var $form = $link.closest('form');

        var notification = mdn.Notifier.growl(gettext('Updating subscription status'), { duration: 0 });

        $link.addClass('disabled');
        $.ajax($form.attr('action'), {
        	cache: false,
        	method: 'post',
        	data: $form.serialize()
        }).done(function(data) {

            var message;
            data = JSON.parse(data);
            if(data.status == 1) {
                $link.text($link.data('unsubscribe-text'));
                message = 'You are now subscribed to this document.';
            }
            else {
                $link.text($link.data('subscribe-text'));
                message = 'You have been unsubscribed from this document.';
            }

            notification.success(gettext(message), 2000);

            $link.removeClass('disabled');
        });
    });

    // Utility method for the togglers
    function setupTogglers($elements) {
        $elements.each(function() {
            var $li = $(this);
            var $sublist = $li.find('> ul, > ol');

            if($sublist.length) {
                $li.addClass('toggleable closed');
                $li.find('> a').addClass('toggler').prepend('<i aria-hidden="true" class="icon-caret-up"></i>');
                $sublist.addClass('toggle-container');
            }
        });
    }

    /*
        Add icons to external links if they don't have images
    */
    $('.external').each(function() {
        var $link = $(this);
        if(!$link.find('img').length) $link.addClass('external-icon');
    });

    /*
        Syntax highlighting scripts
    */
    $('article pre').length && ('querySelectorAll' in doc) && (function() {
        var syntaxScript = doc.createElement('script');
        syntaxScript.setAttribute('data-manual', '');
        syntaxScript.async = 'true';
        syntaxScript.src = mdn.mediaPath + 'js/syntax-prism-min.js?build=' + mdn.build;
        doc.body.appendChild(syntaxScript);
    })();

    /*
        Set up the scrolling TOC effect
    */
    (function() {
        var $toc = $('#toc');
        var tocOffset = $toc.offset();
        var $toggler = $toc.find('> .toggler');
        var fixedClass = 'fixed';
        var $wikiRight = $('#wiki-right');
        var $pageButtons = $('.page-buttons');
        var pageButtonsOffset = $pageButtons.offset();

        // Get button alignment according to text direction
        var buttonDirection = ($('html').attr('dir') == 'rtl') ? 'left' : 'right';

        var scrollFn = debounce(function(e) {
            var scroll = $(doc).scrollTop();
            var pageButtonsHeight = 0;
            var $mainContent = $('.wiki-main-content');

            if(!e || e.type == 'resize') {
                // Calculate right and offset for page buttons on resize and page load
                if(buttonDirection == 'right'){
                    pageButtonsOffset.right = $(win).width() - $mainContent.offset().left - $mainContent.innerWidth();
                }
                // Should the TOC be one-column (auto-closed) or sidebar'd
                if($toc.length){
                    if($toggler.css('pointer-events') == 'auto'    || $toggler.find('i').css('display') != 'none') { /* icon check is for old IEs that don't support pointer-events */
                        // Checking "data-clicked" to ensure we don't override closing/opening if user has done so explicitly
                        if(!$toc.attr('data-closed') && !$toggler.attr('data-clicked')) {
                            $toggler.trigger('mdn:click');
                        }
                    }
                    else if($toc.attr('data-closed')) { // Changes width, should be opened (i.e. mobile to desktop width)
                        $toggler.trigger('mdn:click');
                    }
                }
            }

            // Check if page buttons need to be sticky
            if($pageButtons.attr('data-sticky') == 'true'){
                pageButtonsHeight = $pageButtons.innerHeight();
                if(scroll > pageButtonsOffset.top) {
                    $pageButtons.css('min-width', $pageButtons.css('width'));
                    $pageButtons.css(buttonDirection, pageButtonsOffset[buttonDirection]);
                    $pageButtons.addClass(fixedClass);
                } else {
                    $pageButtons.removeClass(fixedClass);
                }
            }

            // If there is no ToC on the page
            if(!$toc.length) return;

            // Styling for sticky ToC
            var maxHeight = win.innerHeight - parseInt($toc.css('padding-top'), 10) - parseInt($toc.css('padding-bottom'), 10) - pageButtonsHeight;

            if(scroll + pageButtonsHeight > tocOffset.top && $toggler.css('pointer-events') == 'none') {
                $toc.css({
                    width: $toc.css('width'),
                    top: pageButtonsHeight,
                    maxHeight: maxHeight
                });
                $toc.addClass(fixedClass);
            }
            else {
                $toc.css({
                    width: 'auto',
                    maxHeight: 'none'
                });
                $toc.removeClass(fixedClass);
            }

        }, 10);

        // Set it forth!
        if($toc.length || $pageButtons.attr('data-sticky') == 'true'){
            scrollFn();
            $(win).on('scroll resize', scrollFn);
        }
    })();

    /*
        Compat table table setup
    */
    $('.htab').each(function(index) {
            var $htab = $(this);
            var $items = $htab.find('>ul>li');

            $htab.append($('div[id=compat-desktop]')[index]);
            $htab.append($('div[id=compat-mobile]')[index]);

            $items.find('a').on('click mdn:click', function(e) {
                    var $this = $(this);
                    if(e) {
                        e.preventDefault();
                        e.stopPropagation();
                    }
                    $items.removeClass('selected');
                    $this.parent().addClass('selected');
                    $htab.find('>div').hide().eq($items.index($this.parent())).show();
            }).eq(0).trigger('mdn:click');
    });

    /*
        Bottom language checker autosubmit
    */
    $('.wiki-l10n').on('change', function() {
        if(this.value) {
            location = this.value;
        }
    });

    /*
        Adds a context menu to edit page or view history
    */
    $('body[contextmenu=edit-history-menu]').mozContextMenu(function(target, $contextMenu) {
            var $menuitems = $contextMenu.find('menuitem');
            var $body = $('body');
            var isTextSelected = !document.getSelection().isCollapsed;
            var isLinkTargeted = ($(target).is('a') || $(target).parents().is('a'));
            var isImageTargeted = $(target).is('img');

            $body.attr('contextmenu', 'edit-history-menu');

            if(isLinkTargeted || isTextSelected || isImageTargeted) {
                $body.attr('contextmenu', '');
            }

            $contextMenu.on('click', function(e) {
                location.href = (target.href || location.href) + $(e.target).data('action') + '?src=context';
            });
    });

    /*
        Toggle kumascript error detail pane
    */
    $('.kumascript-detail-toggle').toggleMessage({
        toggleCallback: function() {
            $('.kumascript-details').toggleClass('hidden');
        }
    });


    /*
        Stack overflow search form, used for dev program
        ex: http://stackoverflow.com/search?q=[firefox]+or+[firefox-os]+or+[html5-apps]+foobar
    */
    $('.stack-form').html('<form action="http://stackoverflow.com/search"><i class="stack-icon" aria-hidden="true"></i><label for="stack-search" class="offscreen">' + gettext('Search Stack Overflow') + '</label><input id="stack-search" placeholder="' + gettext('Search Stack Overflow') + '" /><button type="submit" class="offscreen">Submit Search</button></form>').find('form').on('submit', function(e) {
        e.preventDefault();

        var value = $(this).find('#stack-search').val();

        if(value != '') {
            win.location = 'http://stackoverflow.com/search?q=[firefox]+or+[firefox-os]+or+[html5-apps]+' + value;
        }
    });

    /*
        if many contributors, dont show all at once.
    */
    (function (){
        var hiddenClass = 'hidden';
        var $contributors = $('.contributor-avatars');
        var $hiddenContributors;
        var $showAllContributors;

        function loadImages(selector) {
            return $contributors.find(selector).mozLazyloadImage();
        }

        // Start displaying first contributors in list
        loadImages('li.shown noscript');

        // Setup "Show all Contributors block"
        if ($contributors.data('has-hidden')) {
            $showAllContributors = $('<button type="button" class="transparent">' + $contributors.data('all-text') + '</button>');

            $showAllContributors.on('click', function(e) {
                e.preventDefault();

                mdn.analytics.trackEvent({
                    category: 'Top Contributors',
                    action: 'Show all'
                });

                // Show all LI elements
                $hiddenContributors = $contributors.find('li.' + hiddenClass);
                $hiddenContributors.removeClass(hiddenClass);

                // Start loading images which were hidden
                loadImages('noscript');

                // Focus on the first hidden element
                $($hiddenContributors.get(0)).find('a').get(0).focus();

                // Remove the "Show all" button
                $(this).remove();

            });

            // Inject the show all button
            $showAllContributors.appendTo($contributors);
        }

        // Track clicks on avatars for the sake of Google Analytics tracking
        $contributors.on('click', 'a', function(e) {
            var newTab = (e.metaKey || e.ctrlKey);
            var href = this.href;
            var data = {
                category: 'Top Contributors',
                action: 'Click position',
                label: index
            };

            if (newTab) {
              mdn.analytics.trackEvent(data);
            } else {
              e.preventDefault();
              mdn.analytics.trackEvent(data, function() { location = href; });
            }
        });

        // Allow focus into and out of the list itself
        $contributors.find('ul').on('focusin focusout', function(e) {
            $(this)[(e.type == 'focusin' ? 'add' : 'remove') + 'Class']('focused');
        });
    })();


    /*
       Bug 981409 - Add some CSS fallback for browsers without MathML support.

       This is based on
       https://developer.mozilla.org/en-US/docs/Web/MathML/Authoring#Fallback_for_Browsers_without)MathML_support
       and https://github.com/fred-wang/mathml.css.
    */
    $('math').length && (function() {
        // Test for MathML support
        var $div = $('<div class="offscreen"><math xmlns="http://www.w3.org/1998/Math/MathML"><mspace height="23px" width="77px"/></math></div>').appendTo(document.body);
        var box = $div.get(0).firstChild.firstChild.getBoundingClientRect();
        $div.remove();

        var supportsMathML = Math.abs(box.height - 23) <= 1 && Math.abs(box.width - 77) <= 1;
        if (!supportsMathML) {
            // Add CSS fallback
            $('<link href="/media/css/libs/mathml.css" rel="stylesheet" type="text/css" />').appendTo(doc.head);

            // Add notification
            $('#wikiArticle').prepend('<div class="notice"><p>' + gettext('Your browser does not support MathML. A CSS fallback has been used instead.') + '</p></div>');
        }
    })();


    /*
        jQuery extensions used within the wiki.
    */
    $.extend({
        // Currently used within CKEDitor YouTube plugin
        parseQuerystring: function(str){
            var nvpair = {};
            var qs = (str || location.search).replace('?', '');
            var pairs = qs.split('&');

            $.each(pairs, function(i, v){
                var pair = v.split('=');
                nvpair[pair[0]] = pair[1];
            });

            return nvpair;
        },
        // Used within the wiki new/move pages
        slugifyString: function(str, allowSlash, allowMultipleUnderscores) {
            var regex = new RegExp('[\?\&\"\'\#\*\$' + (allowSlash ? '' : '\/') + ' +?]', 'g');

            // Remove anything from the slug that could cause big problems
            // "$" is used for verb delimiter in URLs
            var result = str.replace(regex, '_').replace(/\$/g, '');

            // Don't allow "_____" mess
            if(!allowMultipleUnderscores) {
                result = result.replace(/_+/g, '_');
            }

            return result;
        }
    });


    function debounce(func, wait, immediate) {
        var timeout;
        return function() {
            var context = this, args = arguments;
            var later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            var callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    }

    /*
        Track YouTube videos
    */
    (function(){
        var $youtubeIframes = $('iframe[src*="youtube.com/embed"]');
        var players = [];
        var timeoutFlag = 1;
        var timer;

        function timeout() {
            var fraction;
            timeoutFlag = 1;
            $.each(players, function(index, player) {
                if(player.getPlayerState() != 1) return;

                timeoutFlag = 0;

                fraction = player.getCurrentTime() / player.getDuration();

                if(!player.checkpoint) {
                    player.checkpoint = 0.1 + Math.round(fraction * 10) / 10;
                }

                if(fraction > player.checkpoint) {
                    mdn.analytics.trackEvent({
                        category: 'YouTube',
                        action: 'Percent Completed',
                        label: player.getVideoUrl(),
                        value: Math.round(player.checkpoint * 100)
                    });

                    // 10% checkpoints for analytics
                    player.checkpoint += 0.1;
                }
            });

            if(timeoutFlag) {
                timer && clearTimeout(timer);
            }else{
                timer = setTimeout(timeout, 6000);
            }
        };

        // If the page does not have any YouTube videos
        if(!$youtubeIframes.length) return;

        var origin = win.location.protocol + '//' + win.location.hostname +
                    (win.location.port ? ':' + win.location.port: '');

        //Enable JS API on all YouTube iframes, might cause flicker!
        $youtubeIframes.each(function() {
            $(this).attr('src', function(i, src){
                return src + (src.split('?')[1] ? '&':'?') + '&enablejsapi=1&origin=' + origin;
            });
        });

        // Load YouTube Iframe API
        var youtubeScript = doc.createElement('script');
        youtubeScript.async = 'true';
        youtubeScript.src = '//www.youtube.com/iframe_api';
        doc.body.appendChild(youtubeScript);


        // Method executed by YouTube API, needs to be global
        win.onYouTubeIframeAPIReady = function(event) {
            $youtubeIframes.each(function(i){
                players[i] = new YT.Player($(this).get(0));

                players[i].addEventListener('onReady', function(){
                   mdn.analytics.trackEvent({
                        category: 'YouTube',
                        action: 'Load',
                        label: players[i].getVideoUrl()
                    });
                });
                players[i].addEventListener('onStateChange', function(event) {
                    var action;
                    switch(event.data) {
                        case 0: // YT.PlayerState.ENDED
                          action = 'Finished';
                          break;
                        case 1: // YT.PlayerState.PLAYING
                          action = 'Play';
                          if(timeoutFlag){
                            timeout();
                          }
                          break;
                        case 2: // YT.PlayerState.PAUSED
                          action = 'Pause';
                          break;
                        case 3: // YT.PlayerState.BUFFERING
                          action = 'Buffering';
                          break;
                        default:
                          return;
                    }
                    mdn.analytics.trackEvent({
                        category: 'YouTube',
                        action: action,
                        label: players[i].getVideoUrl(),
                    });
                });
                players[i].addEventListener('onPlaybackQualityChange', function(event) {
                    var value;
                    //quality is highres, hd1080, hd720, large, medium and small
                    switch(event.data) {
                        case 'small':
                            value = 240;
                            break;
                        case 'medium':
                            value = 360;
                            break;
                        case 'large':
                            value = 480;
                            break;
                        case 'hd720':
                            value = 720;
                            break;
                        case 'hd1080':
                            value = 1080;
                            break;
                        case 'highres': //higher than 1080p
                            value = 1440;
                            break;
                        default: //undefined
                            value = 0;
                    }
                    mdn.analytics.trackEvent({
                        category: 'YouTube',
                        action: 'Playback Quality',
                        label: players[i].getVideoUrl(),
                        value: value
                    });
                });
                players[i].addEventListener('onError', function(event) {
                    mdn.trackError('YouTube Error: ' + event.data + 'on ' + win.location.href);
                });
            });
        };
    })();
})(window, document, jQuery);
