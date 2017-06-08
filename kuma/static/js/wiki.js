(function(win, doc, $) {
    'use strict';

    /*
        Togglers within articles (i.e.)
    */
    $('.toggleable').mozTogglers();

    /*
        Toggle for quick links with nested lists
    */
    (function() {
        // Set up the quick links with the toggler
        var $quickLinks = $('#quick-links');
        setupTogglers($quickLinks.find('> ul > li, > ol > li'));
        $quickLinks.find('.toggleable').mozTogglers();
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
            if($('.zone-landing-header-preview-base').css('position') === 'absolute') {
                $('.wiki-main-content').css('min-height', $subnav.height());
            }
        }

        minHeightFn();
    });


    /*
        Subscribe / unsubscribe to an article
    */
    $('.page-watch a').on('click', function(e) {
        e.preventDefault();

        var $link = $(this);
        if($link.hasClass('disabled')) return;

        mdn.analytics.trackEvent({
            category: 'Page Watch',
            action: $link.text().trim()
        });

        var $form = $link.closest('form');

        var notification = mdn.Notifier.growl($link.data('subscribe-status'), { duration: 0, type: 'text' });

        $link.addClass('disabled');
        $.ajax($form.attr('action'), {
            cache: false,
            method: 'post',
            data: $form.serialize()
        }).done(function(data) {

            var message;
            if(Number(data.status) === 1) {
                $link.text($link.data('unsubscribe-text'));
                message = $link.data('subscribe-message');
            }
            else {
                $link.text($link.data('subscribe-text'));
                message = $link.data('unsubscribe-message');
            }

            notification.success(message, 2000);

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
        Add intelligent break points to long article titles
    */
    $('#wiki-document-head h1').each(function() {
        var $title = $(this);
        var text = $title.text();
        // split on . - : ( or capital letter, only if followed by 2 letters
        var split = text.split(/(?=[\.:\-\(A-Z][\.:\-\(A-Z]{0,}[a-zA-Z]{3})/g);
        // empty h1
        $title.empty();
        // put array back into h1 seperated by <wbr> tags
        $.each(split, function(key, value) {
            $title.append('<wbr>');
            // add text back, make sure it goes back as text, not code to run
            $title.append(doc.createTextNode(value));
        });
    });

    /*
        Syntax highlighting scripts
    */
    if($('article pre').length && ('querySelectorAll' in doc)) (function() {
        if(mdn.assets && mdn.assets.js.hasOwnProperty('syntax-prism')) {
            mdn.assets.js['syntax-prism'].forEach(function(url, index, array) {
                /*
                   Note: In development, multiple scripts are loaded, and the
                   later scripts use Prism, which is declared in the first
                   script.  This means syntax highlighting often doesn't work
                   on the first page load. Refresh, and syntax highlighing
                   should work.

                   To fix this, we'd have to use something like require.js or
                   in-client merging of JS files.  Maybe django-pipeline will
                   help as well.
                 */
                var syntaxScript = doc.createElement('script');
                syntaxScript.async = array.length === 1;
                if(index === 0) {
                    syntaxScript.setAttribute('data-manual', 'true');
                }
                syntaxScript.src = url;
                doc.head.appendChild(syntaxScript);
            });
        }
    })();

    /*
        Add link to syntax explanations
    */
    (function(){
        // possible syntax languages and links to resources for reading them
        var syntaxSections = {
            css:  {
                link: '/docs/Web/CSS/Value_definition_syntax',
                title: gettext('How to read CSS syntax.'),
                urlTest: '/docs/Web/CSS/',
                classTest: 'brush:css'
            },
            /* these languages do not have syntax articles yet but it's important
                to have the classTest and section tests available when deciding
                if there is a matching language for the purposes of creating the
                link, adding a link and title later will cause them to be linked */
            html: {
                urlTest: '/docs/Web/HTML/',
                classTest: 'brush:html'
            },
            js: {
                urlTest: '/docs/Web/JavaScript/',
                classTest: 'brush:js'
            },
            api: {
                urlTest: '/docs/Web/API/',
                classTest: 'brush:js'
            }
        };

        // check if there is any syntax on the page to add links to
        var $boxes = $('.syntaxbox, .twopartsyntaxbox');

        if($boxes.length) {
            /* run the section and page matching logic
               - isLinkMatch becomes true if we're already on one of the syntax articles
               - sectionMatch becomes the link to a wiki article if we're in a section of
                 the site that has a matching wiki syntax article
             */
            var isLinkMatch = false;
            var sectionMatch;
            for (var section in syntaxSections) {
                var sectionLink = syntaxSections[section].link;
                var sectionTest = syntaxSections[section].urlTest;
                if(window.location.href.indexOf(sectionLink) > -1) {
                    isLinkMatch = true;
                }
                if(window.location.href.indexOf(sectionTest) > -1) {
                    sectionMatch = syntaxSections[section];
                }
            }

            // if we're not already reading an article on syntax...
            if(!isLinkMatch){
                // loop through boxes
                $boxes.each(function() {
                    var $thisBox = $(this);

                    // determine language
                    var syntaxLanguage;

                    // pick CSS if it has class twopartsyntaxbox, this should only ever have CSS in it
                    if($thisBox.hasClass('twopartsyntaxbox')) {
                        syntaxLanguage = syntaxSections.css;
                    }

                    // check if there is a class on the box matching a language (sets to last match)
                    // overrides .twopartsyntaxbox, that's good
                    for (var section in syntaxSections) {
                        var classTest = syntaxSections[section].classTest;
                        if($thisBox.hasClass(classTest)) {
                            syntaxLanguage = syntaxSections[section];
                        }
                    }

                    // if we still don't have a match fall back to the language the section is in
                    if (!syntaxLanguage && sectionMatch) {
                        syntaxLanguage = sectionMatch;
                    }

                    // check we have identified matching help text and links
                    if(syntaxLanguage) {
                        // check that we have the objects we need to add the help text for this language
                        if(syntaxLanguage.link && syntaxLanguage.title) {
                            var syntaxLink = syntaxLanguage.link;
                            var syntaxTitle = syntaxLanguage.title;

                            // add the help text and link to the page
                            var $helpLink = $('<a href="' + syntaxLink + '" class="syntaxbox-help icon-only" lang="en"><i aria-hidden="true" class="icon-question-sign"></i><span>' + syntaxTitle + '</span></a>');
                            $thisBox.before($helpLink);

                            // show help text on mouseover (CSS handles focus)
                            $thisBox.on('mouseenter', function(){$helpLink.addClass('isOpaque');});
                            $thisBox.on('mouseleave', function(){$helpLink.removeClass('isOpaque');});
                        }
                    }
                });
            }
        }
    })();


    /*
        Track clicks on access menu items
    */
    $('#nav-access').on('click contextmenu', 'a', function(event) {
        var $thisLink = $(this);
        var url = $thisLink.attr('href');

        var data = {
            category: 'Access Links',
            action: $thisLink.text(),
            label: $thisLink.attr('href')
        };

        mdn.analytics.trackLink(event, url, data);

        // dimension11 is "skiplinks user"
        if(win.ga) ga('set', 'dimension11', 'Yes');
    });

    /*
        Track clicks on TOC links
    */
    $('#toc').on('click contextmenu', 'a', function(event) {
        var $thisLink = $(this);
        var url = $thisLink.attr('href');

        var linkData = {
            category: 'TOC Links',
            action: $thisLink.text(),
            label: $thisLink.attr('href')
        };

        mdn.analytics.trackLink(event, url, linkData);

        var fixed = $('#toc.fixed').length > 0 ? 'fixed' : 'not fixed';
        var clickData = {
            category: 'TOC Click',
            action: fixed
        };

        mdn.analytics.trackLink(event, url, clickData);
    });

    /*
        Track clicks on main nav links
    */
    $('#main-nav').on('click contextmenu', 'a', function(event) {
        var url = this.href;
        var data = {
            category: 'Wiki',
            action: 'Main Nav',
            label: url
        };

        mdn.analytics.trackLink(event, url, data);
    });

    /*
        Track clicks on Crumb links
    */
    $('.crumbs').on('click contextmenu', 'a', function(event) {
        var url = this.href;
        var data = {
            category: 'Wiki',
            action: 'Crumbs',
            label: url
        };

        mdn.analytics.trackLink(event, url, data);
    });


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

        var stickyFeatureEnabled = $pageButtons.attr('data-sticky') === 'true';

        // Get button alignment according to text direction
        var buttonDirection = ($('html').attr('dir') === 'rtl') ? 'left' : 'right';

        var scrollFn = debounce(function(e) {
            var scroll = $(doc).scrollTop();
            var pageButtonsHeight = 0;
            var $mainContent = $('.wiki-main-content');

            var pointerEvents = $toggler.css('pointer-events');

            if(!e || e.type === 'resize') {
                // Calculate right and offset for page buttons on resize and page load
                if(buttonDirection === 'right'){
                    pageButtonsOffset.right = $(win).width() - $mainContent.offset().left - $mainContent.innerWidth();
                }
                // Should the TOC be one-column (auto-closed) or sidebar'd
                if($toc.length){
                    if(pointerEvents === 'auto' || $toggler.find('i').css('display') !== 'none') { /* icon check is for old IEs that don't support pointer-events */
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
            if(stickyFeatureEnabled){
                pageButtonsHeight = $pageButtons.innerHeight();
                if(scroll > pageButtonsOffset.top) {
                    $pageButtons.addClass(fixedClass);

                    // Only do the fixed positioning if the stylesheet says to
                    // i.e. don't fix buttons to top while scrolling if on smaller device
                    if(($pageButtons.css('position') === 'fixed')) {
                        $pageButtons.css('min-width', $pageButtons.css('width'));
                        $pageButtons.css(buttonDirection, pageButtonsOffset[buttonDirection]);
                    }
                } else {
                    $pageButtons.removeClass(fixedClass);
                }
            }

            // If there is no ToC on the page
            if(!$toc.length) return;

            // Styling for sticky ToC
            var maxHeight = win.innerHeight - parseInt($toc.css('padding-top'), 10) - parseInt($toc.css('padding-bottom'), 10) - pageButtonsHeight;
            if((scroll + pageButtonsHeight > tocOffset.top) && pointerEvents === 'none') {
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

        }, 15);

        // Set it forth!
        if($toc.length || stickyFeatureEnabled){
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
            win.location = this.value;
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

            if(isLinkTargeted || isTextSelected || isImageTargeted) {
                $body.attr('contextmenu', '');
            }

            $contextMenu.on('click', function(e) {
                location.href = $(e.target).data('action') + '?src=context';
            });
    });

    /*
        Kumascript error detected
    */
    // is there an error?
    var $kserrors = $('#kserrors');
    if($kserrors.length){
        // enable the details toggle
        var $kserrorsToggle = $kserrors.find('.kserrors-details-toggle');
        var $kserrorsDetails = $kserrors.find('.kserrors-details');
        $kserrorsToggle.toggleMessage({
            toggleCallback: function() {
                $kserrorsDetails.toggleClass('hidden');
            }
        });
        // loop through error list and log errors
        var $kserrorsList = $('#kserrors-list');
        if($kserrorsList.length){
            $kserrorsList.each(function(){
                var $thisError = $(this);
                var errorType = $thisError.find('.kserror-type').text().trim();
                var errorMacro = $thisError.find('.kserror-macro').text().trim();
                var errorParse = $thisError.find('.kserror-parse').text().trim().replace(/\s\s+/g, ' ');
                mdn.analytics.trackError('Kumascript Error', errorType, 'in: ' + errorMacro + '; parsing: ' + errorParse );
            });
        } else {
            // generic error recorded - no details if user not logged in
            mdn.analytics.trackError('Kumascript Error', 'generic error');
        }
    }

    /*
        Track untranslated pages
    */
    // is there an translation banner?
    var $docPending = $('#doc-pending-fallback');
    if($docPending.length){
        mdn.analytics.trackError('Translation Pending', 'displayed');
    }

    /*
        Stack overflow search form, used for dev program
        ex: http://stackoverflow.com/search?q=[firefox]+or+[firefox-os]+or+[html5-apps]+foobar
    */
    $('.stack-form').html('<form action="http://stackoverflow.com/search"><i class="stack-icon" aria-hidden="true"></i><label for="stack-search" class="offscreen">' + gettext('Search Stack Overflow') + '</label><input id="stack-search" placeholder="' + gettext('Search Stack Overflow') + '" /><button type="submit" class="offscreen">Submit Search</button></form>').find('form').on('submit', function(e) {
        e.preventDefault();

        var value = $(this).find('#stack-search').val();

        if(value !== '') {
            win.location = 'http://stackoverflow.com/search?q=[firefox]+or+[firefox-os]+or+[html5-apps]+' + value;
        }
    });

    /*
        if many contributors, dont show all at once.
    */
    (function (){
        var hiddenClass = 'hidden';
        var shownClass = 'shown';
        var $contributors = $('.contributor-avatars');
        var $showAllContributors;

        function loadImages(selector) {
            return $contributors.find(selector).mozLazyloadImage();
        }

        function initToggle() {
            $showAllContributors = $('<button id="contributors-toggle" type="button" class="transparent" data-alternate-message="' + $contributors.data('alternate-message') + '">' + $contributors.data('all-text') + '</button>');

            // toggle message and state of hidden
            $showAllContributors.toggleMessage({
                toggleCallback: toggleImages
            });

            // Inject the show all button
            $showAllContributors.appendTo($contributors);
        }

        function toggleImages() {
            var $hiddenContributors;
            $hiddenContributors = $contributors.find('li.' + hiddenClass);
            $contributors.toggleClass('contributor-avatars-open');
            if($hiddenContributors.length) {
                mdn.analytics.trackEvent({
                    category: 'Top Contributors',
                    action: 'Show all'
                });

                // Show all LI elements
                $hiddenContributors.removeClass(hiddenClass);

                // Start loading images which were hidden
                loadImages('noscript');
            } else {
                $contributors.find('li:not(.' + shownClass + ')' ).addClass(hiddenClass);
            }
        }


        // Track clicks on avatars for the sake of Google Analytics tracking
        $contributors.on('click', 'a', function(event) {
            var url = this.href;
            var index = $(this).parent().index() + 1;
            var data = {
                category: 'Top Contributors',
                action: 'Click position',
                label: index
            };

            mdn.analytics.trackLink(event, url, data);
        });

        // Don't bother with contributor bar if it starts hidden
        if($contributors.css('display') === 'none') return;

        // Start displaying first contributors in list
        loadImages('li.' + shownClass + ' noscript');


        // Setup "Show all Contributors block"
        if ($contributors.data('has-hidden')) {
            initToggle();
        }

        // Trigger CSS on focus into and out of the list itself
        $contributors.find('ul').on('focusin focusout', function(event) {
            $(this)[(event.type === 'focusin' ? 'add' : 'remove') + 'Class']('focused');
        });
    })();


    /*
       Bug 981409 - Add some CSS fallback for browsers without MathML support.

       This is based on
       https://developer.mozilla.org/en-US/docs/Web/MathML/Authoring#Fallback_for_Browsers_without)MathML_support
       and https://github.com/fred-wang/mathml.css.
    */
    if($('math').length) (function() {
        // Test for MathML support
        var $div = $('<div class="offscreen"><math xmlns="http://www.w3.org/1998/Math/MathML"><mspace height="23px" width="77px"/></math></div>').appendTo(document.body);
        var box = $div.get(0).firstChild.firstChild.getBoundingClientRect();
        $div.remove();

        var supportsMathML = Math.abs(box.height - 23) <= 1 && Math.abs(box.width - 77) <= 1;
        if (!supportsMathML) {
            // Add CSS fallback
            $('<link href="' + mdn.staticPath + 'styles/libs/mathml.css" rel="stylesheet" type="text/css" />').appendTo(doc.head);

            // Add notification
            $('#wikiArticle').prepend('<div class="notice"><p>' + gettext('Your browser does not support MathML. A CSS fallback has been used instead.') + '</p></div>');
        }
    })();

    /*
      Make Compare selected revisions button sticky when scrolling history page
    */
    (function() {
        var $button = $('.revision-list-controls .link-btn');
        if($button.length) {
            var revisionButtonOffset = $button.offset().top;
            $(win).on('scroll', function() {
                var $compareButton = $button;
                var scroll = $(this).scrollTop();
                $compareButton.toggleClass('fixed', scroll >= revisionButtonOffset);
            });
        }
    })();

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
                if(player.getPlayerState() !== 1) return;

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
                if(timer) clearTimeout(timer);
            }else{
                timer = setTimeout(timeout, 6000);
            }
        }

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
                        label: players[i].getVideoUrl()
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
                    mdn.analytics.trackError('YouTube Error', event.data);
                });
            });
        };
    })();

    // Make <summary> and <details> tags work even if the browser doesn't support them.
    // From http://mathiasbynens.be/notes/html5-details-jquery
    function initDetailsTags() {
        // test for browser support of details from http://mathiasbynens.be/notes/html5-details-jquery
        var supportsDetails = (function(doc) {
            var el = doc.createElement('details');
            var isFake;
            var root;
            var diff;
            if (!('open' in el)) {
                return false;
            }
            root = doc.body || (function() {
                var de = doc.documentElement;
                isFake = true;
                return de.insertBefore(doc.createElement('body'), de.firstElementChild || de.firstChild);
            }());
            el.innerHTML = '<summary>a</summary>b';
            el.style.display = 'block';
            root.appendChild(el);
            diff = el.offsetHeight;
            el.open = true;
            diff = diff != el.offsetHeight;
            root.removeChild(el);
            if (isFake) {
                root.parentNode.removeChild(root);
            }
            return diff;
        }(document));

        // No reason to move further if details are supported!
        if(supportsDetails) return;

        // Note <details> tag support. Modernizr doesn't do this properly as of 1.5; it thinks Firefox 4 can do it, even though the tag has no "open" attr.
        $('details').addClass('no-details').each(function() {
            // Store a reference to the current `details` element in a variable
            var $details = $(this);
            // Store a reference to the `summary` element of the current `details` element (if any) in a variable
            var $detailsSummary = $('summary', $details);
            // Do the same for the info within the `details` element
            var $detailsNotSummary = $details.children(':not(summary)');
            // This will be used later to look for direct child text nodes
            var $detailsNotSummaryContents = $details.contents(':not(summary)');

            // If there is no `summary` in the current `details` element...
            if (!$detailsSummary.length) {
                // ...create one with default text
                $detailsSummary = $(doc.createElement('summary')).text(gettext('Details')).prependTo($details);
            }

            // Look for direct child text nodes
            if ($detailsNotSummary.length !== $detailsNotSummaryContents.length) {
                // Wrap child text nodes in a `span` element
                $detailsNotSummaryContents.filter(function() {
                    // Only keep the node in the collection if it's a text node containing more than only whitespace
                    return (this.nodeType === 3) && (/[^\t\n\r ]/.test(this.data));
                }).wrap('<span>');
                // There are now no direct child text nodes anymore -- they're wrapped in `span` elements
                $detailsNotSummary = $details.children(':not(summary)');
            }

            // Hide content unless there's an `open` attribute
            if (typeof $details.attr('open') !== 'undefined') {
                $details.addClass('open');
                $detailsNotSummary.show();
            } else {
                $detailsNotSummary.hide();
            }

            // add ARIA, tabindex, listeners and events
            $detailsSummary.attr('tabindex', 0).attr('role', 'button').on('click', function() {
                // Focus on the `summary` element
                $detailsSummary.focus();
                // Toggle the `open` attribute of the `details` element
                if (typeof $details.attr('open') !== 'undefined') {
                    $details.removeAttr('open');
                    $detailsSummary.attr('aria-expanded', 'false');
                } else {
                    $details.attr('open', 'open');
                    $detailsSummary.attr('aria-expanded', 'true');
                }
                // Toggle the additional information in the `details` element
                $detailsNotSummary.slideToggle();
                $details.toggleClass('open');
            }).on('keyup', function(ev) {
                if (32 == ev.keyCode || 13 == ev.keyCode) {
                    // Opera already seems to trigger the `click` event when Enter is pressed
                    ev.preventDefault();
                    $detailsSummary.click();
                }
            });
        });
    }


    if($('details').length){
        initDetailsTags();
    }


    /**
     * Generates a storage key based on pathname
     * copied from wiki-edit-draft.js because: race conditions
     * does not need to copy logic for dealing with new translations
     */
    function getDraftStorageKey() {
        // start with path
        var key = win.location.pathname;
        // remove $vars
        key = key.replace('$edit', '');
        key = key.replace('$translate', '');
        key = 'draft/edit' + key;
        key = $.trim(key);
        return key;
    }

    // check for rev_saved in query string
    var revisionSaved = win.mdn.getUrlParameter('rev_saved');
    var storageKey = getDraftStorageKey();
    if(win.location.href.indexOf('rev_saved') > -1 && win.mdn.features.localStorage) {
        var draftRevision = localStorage.getItem(storageKey + '#revision');
        // check for drafts matching query string
        if (draftRevision === revisionSaved) {
            // delete matching draft, save-time, and revisionId
            localStorage.removeItem(storageKey);
            localStorage.removeItem(storageKey + '#save-time');
            localStorage.removeItem(storageKey + '#revision');
        }
        // remove query string
        var location = win.location;
        if (win.history.replaceState) {
            win.history.replaceState({}, '', location.pathname);
        }
    }

})(window, document, jQuery);
