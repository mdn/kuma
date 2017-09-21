(function(win, doc, $) {
    'use strict';

    var focusClass = 'focused';
    var noop = function(){};

    /*
        Plugin to create nav menus, show/hide delays, etc.
        Accessible by keyboard too!
    */
    $.fn.mozMenu = function(options) {

        var settings = $.extend({
            showDelay: 100,
            hideDelay: 100,
            fadeInSpeed: null,
            fadeOutSpeed: null,
            submenu: null,
            focusOnOpen: false,
            brickOnClick: false,
            onOpen: noop,
            onClose: noop
        }, options);

        var closeTimeout;
        var showTimeout;

        return this.each(function() {
            var $self = $(this);
            var $parent = $self.parent();
            var initialized;

            // Find the trigger element's submenu
            var $submenu = $self.submenu = (settings.submenu || $parent.find('.js-submenu'));

            // Prevent the default behavior of the trigger element if this is set
            var brick = settings.brickOnClick;
            if(brick && $submenu.length) {
                $self.on('click', function(e) {
                    if((typeof brick === 'function' && brick(e)) || brick) e.preventDefault();
                });
            }

            // Provide the settings to both the submenu and item as either can be found independently
            // The settings for the current menu and the "$.fn.mozMenu.$openMenu" can be different
            $self.settings = $submenu.settings = settings;

            // Add a mouseenter / focus event to get the showing of the submenu in motion
            var assumeMobile = false;
            $self.on('touchstart mouseenter focus', function(startEvent) {
                if(startEvent.type === 'touchstart') {
                    startEvent.stopImmediatePropagation();
                    if($self.submenu.length) {
                        startEvent.preventDefault();
                    }
                    assumeMobile = true;
                }

                // If this is a fake focus set by us, ignore this
                if($submenu.ignoreFocus) return;

                // If no submenu, go
                if(!$submenu.length) {
                    clear(showTimeout);
                    if($.fn.mozMenu.$openMenu) closeSubmenu($.fn.mozMenu.$openMenu.submenu);
                    return;
                }

                // Lazy-initialize events that aren't needed until an item is entered.
                if(!initialized) {
                    initialized = 1;

                    // Add the close
                    var $closeButton = $('<button type="button" class="submenu-close transparent">' +
                        '<span class="offscreen">' + gettext('Close submenu') + '</span>' +
                        '<i aria-hidden="true" class="icon-times"></i>' +
                    '</button>').appendTo($submenu);

                    // Hide the submenu when the main menu is blurred for hideDelay
                    $self.on('mouseleave focusout', function() {
                        clear(showTimeout);
                        closeSubmenu($submenu);
                    });

                    // Hide the submenu when the submenu is blurred for hideDelay
                    $submenu.on('mouseleave focusout', function(e) {
                        // "focuseout" is firing on child elements and sending off a bunch of moot
                        // close requests, so we stop that
                        if(e.type === 'focusout' && e.target !== $submenu.get(0)) return;

                        clear(showTimeout);
                        closeSubmenu($submenu);
                    });

                    // Cancel the close timeout if moving from main menu item to submenu
                    if(!assumeMobile) {
                        $submenu.on('mouseenter focusin', function() {
                            clear(closeTimeout);
                        });
                    }

                    // Close if it's the last link and they press tab *or* the hit escape
                    $submenu.on('keyup', function(e) {
                        if(e.keyCode === 27) { // Escape
                            closeSubmenu($submenu);
                            $submenu.ignoreFocus = true;
                            setTimeout(function() { $submenu.ignoreFocus = false; }, 10);
                            $self[0].focus();
                        }
                    });

                    // Close button should close the submenu
                    $closeButton.on('click', function(){
                        closeSubmenu($submenu || $(this).parent());
                    });
                }

                // If there's an open submenu and it's not this one, close it
                // Used for tab navigation from submenu to the next menu item
                if($.fn.mozMenu.$openMenu && $.fn.mozMenu.$openMenu !== $self) {
                    clear(showTimeout);
                    closeSubmenu($.fn.mozMenu.$openMenu.submenu);
                }
                else if($.fn.mozMenu.$openMenu === $self) {
                    clear(closeTimeout);
                }

                // Keep the open menu on this fn itself so only one menu can be open at any time,
                // regardless of the instance or menu group
                $.fn.mozMenu.$openMenu = $self;

                // Show my submenu after the showDelay
                showTimeout = setTimeout(function() {
                    // Setting z-index here so that current menu is always on top
                    $submenu.css('z-index', 99999).addClass('open').attr('aria-hidden', 'false').fadeIn($submenu.settings.fadeInSpeed);

                    // track opening
                    mdn.analytics.trackEvent({
                        category: 'MozMenu',
                        action: $submenu.attr('id')
                    });

                    // Find the first link for improved usability
                    if($submenu.settings.focusOnOpen) {
                        var firstLink = $submenu.find('a').get(0);
                        if(firstLink) {
                            try { // Putting in try/catch because of opacity/focus issues in IE
                                $(firstLink).addClass(focusClass);
                                firstLink.focus();
                            }
                            catch(e){
                                console.log('Menu focus exception! ', e);
                            }
                        }
                    }
                    $submenu.settings.onOpen();
                }, $submenu.settings.showDelay);
            });
        });

        /* Gets the open parent (un-used)
        function getOpenParent() {
            return $.fn.mozMenu.$openMenu.submenu;
        }
        */

        // Clears the current timeout, interrupting fade-ins and outs as necessary
        function clear(timeout) {
            if(timeout) clearTimeout(timeout);
        }

        // Closes a given submenu
        function closeSubmenu($sub) {
            closeTimeout = setTimeout(function() {
                // Set the z-index to one less so another menu would get top spot if overlapping and opening
                if($sub) {
                    $sub.css('z-index', 99998)
                            .removeClass('open')
                            .attr('aria-hidden', 'true')
                            .fadeOut($sub.settings.fadeOutSpeed, function() {
                                $sub.settings.onClose();
                            });
                }
            }, $sub.settings.hideDelay);
        }
    };

    /*
        Plugin to listen for special keyboard keys and will fire actions based on them
    */
    $.fn.mozKeyboardNav = function(options) {
        var settings = $.extend({
            itemSelector: 'a',
            onEnterKey: noop,
            alwaysCollectItems: false
        }, options);

        var $selectedItem;

        return this.each(function() {

            var $items = $(this).find(settings.itemSelector);
            if(!$items.length) return;

            var $self = $(this);

            $self.on('keydown', function(e) {
                var code = e.keyCode;
                var charCode = e.charCode;
                var numberKeyStart = 49;

                // If we should always get fresh items, do so
                if(settings.alwaysCollectItems) {
                    $items = $(this).find(settings.itemSelector);
                    $selectedItem = null;
                }

                // Up and down buttons
                if(code === 38 || code === 40) {
                    e.preventDefault();
                    e.stopPropagation();

                    // Find currently selected item and clear
                    $selectedItem = $items.filter('.' + focusClass).removeClass(focusClass);

                    // Tricky...if they clicked elsewhere in the mean time, we may need to try to
                    // figure it out by activeElement
                    var index = $items.index($selectedItem);
                    var activeElementIndex = doc.activeElement && $items.index(doc.activeElement);
                    if(activeElementIndex > -1) {
                        index = activeElementIndex;
                    }
                    if(index < 0) {
                        index = 0;
                    }

                    // If nothing is currently selected, start with first no matter which key
                    var $next = $($items.get(index + 1));
                    var $prev = $($items.get(index - 1));

                    if(code === 38) {    // up
                        if($prev.length) selectItem($prev);
                    }
                    else if(code === 40) {    // down
                        selectItem($next.length ? $next : $items.first());
                    }
                }
                // Number keys: 1, 2, 3, etc.
                else if(charCode >= numberKeyStart && charCode <= 57) {
                    var item = $items.get(charCode - numberKeyStart);
                    if(item) selectItem(item);
                }
                // Enter key
                else if(code === 13) {
                    $selectedItem = $(e.target);
                    settings.onEnterKey($selectedItem);
                }
            });

        });

        function selectItem(item) {
            $(item).addClass(focusClass).get(0).focus();
            $selectedItem = item;
        }

    };

    /*
        Plugin to listen for special keyboard keys and will fire actions based on them
    */
    $.fn.mozTogglers = function(options) {
        var settings = $.extend({
            onOpen: noop,
            slideCallback: noop,
            duration: 200 /* 400 is the default for jQuery */
        }, options);

        this.each(function() {
            var $self = $(this);
            var pieces = getTogglerComponents($self);
            var closedAttribute = 'data-closed';

            // Initialize open / close for the purpose of animation
            if($self.hasClass('closed')) {
                $self.attr(closedAttribute, 'true').removeClass('closed');
                pieces.$container.hide();
            }
            setIcon(pieces.$toggler, $self);

            // Add aria to indicate dropdown menu
            pieces.$toggler.attr('aria-haspopup', true);

            // Close on ESC
            $self.on('keyup', '.toggle-container', function(e) {
                e.preventDefault();
                e.stopPropagation();
                if(e.keyCode === 27) {
                    $(this).siblings('a').trigger('mdn:click').focus();
                }
            });

            // Click event to show/hide
            $self.on('click mdn:click', '.toggler', function(e) {
                e.preventDefault();
                e.stopPropagation();
                settings.onOpen.call(this);

                // If a true click, mark toggler as such so automated togger clicks (like toc) know not to
                // close without user consent
                if(e.type === 'click') {
                    $(this).attr('data-clicked', true);
                }

                // If I'm an accordion, close the other one
                var $parent = $self.closest('ol, ul');
                if($parent.hasClass('accordion')) {
                    var $current = $parent.find('> .current');
                    if($current.length && $current.get(0) !== $self.get(0)) {
                        toggle($current, true);
                    }
                }

                // Open or close the item, set the icon, etc.
                toggle($self);
            });

            // The toggler can be initially opened via a data- attribute
            //if($self.attr('data-default-state') === 'open') {
            //   toggle($self);
            //}

            function toggle($li, forceClose) {
                var pieces = getTogglerComponents($li);

                if(!getState($li) || forceClose) {
                    $li.attr(closedAttribute, 'true').removeClass('current');
                    pieces.$container.attr('aria-expanded', false);
                    pieces.$container.slideUp(settings.duration, settings.slideCallback);
                }
                else {
                    $li.attr(closedAttribute, '').addClass('current');
                    pieces.$container.attr('aria-expanded', true);
                    pieces.$container.slideDown(settings.duration, settings.slideCallback);
                }
                setIcon(pieces.$toggler, $li);
            }

            function getTogglerComponents($li) {
                return {
                    $container: $li.find('> .toggle-container'),
                    $toggler: $li.find('> .toggler')
                };
            }

            function setIcon($tog, $li) {
                var openIcon = $tog.attr('data-open-icon') || 'icon-plus-circle';
                var closedIcon = $tog.attr('data-closed-icon') || 'icon-minus-circle';
                $tog.find('i').attr('class', (getState($li) ? openIcon : closedIcon));
            }

            function getState($li) {
                return $li.attr(closedAttribute);
            }
        });
    };

    /*
        Plugin to adds a native html5 contextmenu
        Callback passes two arguments, event.target and the menu-element
    */
    $.fn.mozContextMenu = function(callback) {
        return this.on('contextmenu', function(e) {
            callback(e.target, $('#' + $(this).attr('contextmenu')));
        });
    };

    /*
        Plugin to lazyload images
    */
    $.fn.mozLazyloadImage = function() {
        return this.each(function() {
            var $img = $('<img />');
            var alt = $(this).data('alt');

            $img.on('load', function() {
                $(this)
                    .attr('alt', alt)
                    .addClass('loaded');
            });
            $.each($(this).data(), function(name, value) {
                if (name !== 'alt') {
                    $img.attr(name, value);
                }
            });
            $(this).after($img).remove();
        });
    };

    /*
        Plugin to toggle button messages
    */
    $.fn.toggleMessage = function(options){
        var settings = $.extend({
            event: 'click',
            toggleCallback: noop
        }, options);

        return this.each(function(){
            $(this).on(settings.event, function(e){
                var $self = $(this);
                e.preventDefault();
                var currentMessage = $self.text();
                var alternateMessage = $self.attr('data-alternate-message');
                $self.attr('data-alternate-message', currentMessage)
                       .html(alternateMessage);
                settings.toggleCallback();
            });
        });
    };

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
            var regex = new RegExp('[?&\"\'#*$' + (allowSlash ? '' : '\/') + ' +?]', 'g');

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


    win.mdn.Notifier = (function() {
        // Hold onto the one tray
        var $tray;
        var defaults = {
            classes: '', // Classes to apply to the individual notification
            closable: false, // Should the "x" icon appear
            level: 'info', // Should the icon appear when a state is given
            duration: 3000, // How long should the item be shown?  '0' means the message needs to be removed manually or via the handle.
            url: null, // Should clicking the item go anywhere?
            onclick: null, // What should happen if they click on the notification?
            onclose: null, // What should happen upon closing of individual notification?
            type: 'html' // html or text?
        };

        var processedKey = 'data-processed';
        var defaultState = { state: 'info', className: 'info', iconName: 'icon-info-sign'  };
        var states = [
            { state: 'success', className: 'success', iconName: 'icon-smile' },
            { state: 'error', className: 'error', iconName: 'icon-frown' },
            { state: 'warning', className: 'warning', iconName: 'icon-warning-sign'  },
            { state: 'question', className: 'question', iconName: 'icon-question-sign'  },
            defaultState
        ];
        var statesObj = {};
        $.each(states, function() {
            statesObj[this.state] = this;
        });

        // Closes an item
        function closeItem($item, callback) {
            $item.fadeOut(300, function() {
                $item.addClass('closed');
                if(callback) callback.apply($item, null);
            });
        }

        // Updates an item's HTML
        function updateMessageHTML($item, message) {
            $item.find('.notification-message').html(message);
        }

        function updateMessageText($item, message) {
            $item.find('.notification-message').text(message);
        }

        // Enacts options upon an item, used by both discover and growl
        function applyOptions($item, options) {
            // Don't process a notification more than once
            if($item.attr(processedKey)) {
                return;
            }
            $item.attr(processedKey, true);

            // Populating notification content via vanilla JS so we don't lose any
            // attached events to elements within the message itself
            // The jQuery version is ugly: http://stackoverflow.com/a/4399718
            var $messageWrapper = $('<div class="notification-message"></div>');
            var children = $item.get(0).childNodes;
            while(children && children.length) {
                $messageWrapper.get(0).appendChild(children[0]);
            }
            $messageWrapper.appendTo($item);

            // Add an icon if needed
            var icon = defaultState.iconName;
            if(statesObj[options.level]) {
                icon = statesObj[options.level].iconName;
            }
            if(options.level) {
                $item.addClass(options.level);
            }

            $item.prepend('<div class="notification-img"><i aria-hidden="true" class="'+ icon +'"></i></div>');

            // Add URL click event
            if(options.url) {
                $item.addClass('clickable').on('click', function() {
                    win.location = defaults.url;
                });
            }

            // Add desired css class
            $item.addClass(options.classes);

            // Add item's close and click event if needed
            if(options.closable) {
                $('<button class="close" title="' + gettext('Close notification') + '"><i class="icon-remove" aria-hidden="true"></i></button>').on('click', function(e) {
                    e.stopPropagation();
                    e.preventDefault();

                    closeItem($item, options.onclose);
                }).appendTo($item);
            }

            // Click event for notifications
            if(options.onclick) {
                $item.addClass('clickable').on('click', options.onclick);
            }

            // Add automatic closer
            if(options.duration) setTimeout(function() {
                closeItem($item, options.onclose);
            }, options.duration);
        }

        // The actual Notifier object component
        return {
            // Finds notifications under a given parent,
            discover: function(parent) {
                var $notifications = $(parent || doc.body).find('.notification:not([' + processedKey + '])');
                $notifications.each(function() {
                    var $item = $(this);
                    applyOptions($item, $item.data());
                });

                return $notifications;
            },
            growl: function(message, options) {
                var updateFunc = updateMessageHTML;

                // Create the tray for the first message
                if(!$tray) {
                    $tray = $('<div class="notification-tray" role="status" aria-live="polite"></div>').appendTo(doc.body);
                }

                // Merge options with defaults
                options = $.extend({}, defaults, options || {});

                if (options.type === 'text') {
                    updateFunc = updateMessageText;
                }
                // Create the growl message, add to tray
                var $item = $('<div class="notification">' + message + '</div>');

                // Apply options and format notification
                applyOptions($item, options);

                // Show within the container
                $item.prependTo($tray);

                // Return a handle for the growl item
                var handle = {
                    item: $item,
                    options: options,
                    updateMessage: function(message) {
                        updateFunc(this.item, message);
                        return this;
                    },
                    close: function(delay, callback) {
                        $item = this.item;
                        delay = delay || options.duration;
                        callback = callback || options.onclose;

                        if(delay) {
                            setTimeout(function() {
                                closeItem($item, callback);
                            }, delay);
                        }
                        else {
                            closeItem($item, callback);
                        }
                        return this;
                    }
                };

                // Add success, fail, warning, and info methods to the handle
                $.each(states, function() {

                    var stateObj = this;
                    var state = this.state;
                    var className = this.className;
                    handle[state] = function(message, delay) {
                        var $item = handle.item;

                        $item.addClass(className);
                        $item.find('.notification-img i').attr('class', stateObj.iconName);

                        if(message) updateFunc($item, message);
                        if(delay) this.close(delay);

                        return this;
                    };
                });

                return handle;
            }
        };
    })();

})(window, document, jQuery);
