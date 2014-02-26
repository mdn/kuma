(function($) {

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
      submenu: null,
      focusOnOpen: false,
      brickOnClick: false,
      onOpen: noop,
      onClose: noop
    }, options);

    var closeTimeout;
    var showTimeout;

    return $(this).each(function() {
      var $self = $(this);
      var $li = $self.parent();
      var initialized;

      // Brick on click?
      var brick = settings.brickOnClick;
      if(brick) {
        $self.on('click', function(e) {
          if(typeof brick != 'function' || brick(e)) e.preventDefault();
        });
      }

      // Find a submenu.  If one doesn't exist, no need to go further
      var $submenu = (settings.submenu || $li.find('.submenu'));

      // Add a mouseenter / focus event to get the showing of the submenu in motion
      $self.on('mouseenter focus', function() {
        // If this is a fake focus set by us, ignore this
        if($submenu.ignoreFocus) return;

        // If no submenu, go
        if(!$submenu.length) {
          clear(showTimeout);
          $.fn.mozMenu.$openMenu && closeSubmenu($.fn.mozMenu.$openMenu.parent().find('.submenu'));
          return;
        }

        // Lazy-initialize events that aren't needed until an item is entered.
        if(!initialized) {
          initialized = 1;

          // Hide the submenu when the main menu is blurred for hideDelay
          $self.on('mouseleave focusout', function() {
            clear(showTimeout);
            closeSubmenu($submenu);
          });

          // Hide the submenu when the submenu is blurred for hideDelay
          $submenu.on('mouseleave', function() {
            clear(showTimeout);
            closeSubmenu($submenu);
          });

          // Cancel the close timeout if moving from main menu item to submenu
          $submenu.on('mouseenter focusin', function() {
            clear(closeTimeout);
          });

          // Close if it's the last link and they press tab *or* the hit escape
          $submenu.on('keyup', function(e) {
            if(e.keyCode == 27) { // Escape
              closeSubmenu($submenu);
              $submenu.ignoreFocus = true;
              setTimeout(function() { $submenu.ignoreFocus = false; }, 10);
              $self[0].focus();
            }
          });
          
          $submenu.find('.submenu-close').on('click', function(){
            closeSubmenu($(this).parent());
          });
        }
        // If there's an open submenu and it's not this one, close it
        // Used for tab navigation from submenu to the next menu item
        if($.fn.mozMenu.$openMenu && $.fn.mozMenu.$openMenu != $self) {
          clear(showTimeout);
          closeSubmenu($.fn.mozMenu.$openMenu.parent().find('.submenu'));
        }
        else if($.fn.mozMenu.$openMenu == $self) {
          clear(closeTimeout);
        }

        // Keep the open menu on this fn itself so only one menu can be open at any time,
        // regardless of the instance or menu group
        $.fn.mozMenu.$openMenu = $self;

        // Show my submenu after the showDelay
        showTimeout = setTimeout(function() {
          // Setting z-index here so that current menu is always on top
          $submenu.css('z-index', 99999).addClass('open').attr('aria-hidden', 'false').fadeIn();

          // Find the first link for improved usability
          if(settings.focusOnOpen) {
            var firstLink = $submenu.find('a').get(0);
            if(firstLink) {
              try { // Putting in try/catch because of opacity/focus issues in IE
                $(firstLink).addClass(focusClass) && firstLink.focus();
              }
              catch(e){
                console.log('Exception! ', e);
              }
            }
          }
          settings.onOpen();
        }, settings.showDelay);
      });
    });

    // Clears the current timeout, interrupting fade-ins and outs as necessary
    function clear(timeout) {
      timeout && clearTimeout(timeout);
    }

    // Closes a given submenu
    function closeSubmenu($sub) {
      closeTimeout = setTimeout(function() {
        // Set the z-index to one less so another menu would get top spot if overlapping and opening
        $sub && $sub.css('z-index', 99998).removeClass('open').attr('aria-hidden', 'true').fadeOut();
        settings.onClose();
      }, settings.hideDelay);
    }
  };

  /*
    Plugin to listen for special keyboard keys and will fire actions based on them
  */
  $.fn.mozKeyboardNav = function(options) {
    var settings = $.extend({
      itemSelector: 'a'
    }, options);

    return $(this).each(function() {

      var $items = $(this).find(settings.itemSelector);
      if(!$items.length) return;

      var $self = $(this);

      $self.on('keydown', function(e) {
        var code = e.keyCode;
        var charCode = e.charCode;
        var numberKeyStart = 49;

        if(code == 38 || code == 40) {
          e.preventDefault();
          e.stopPropagation();

          // Find currently selected item and clear
          var $selectedItem = $items.filter('.' + focusClass).removeClass(focusClass);

          // If nothing is currently selected, start with first no matter which key
          var index = $items.index($selectedItem) || 0;
          var $next = $($items.get(index + 1));
          var $prev = $($items.get(index - 1));

          if(code == 38) {  // up
            $prev.length && selectItem($prev);
          }
          else if(code == 40) {  // down
            selectItem($next.length ? $next : $items.first());
          }
        }
        else if(charCode >= numberKeyStart && charCode <= 57) {
          var item = $items.get(charCode - numberKeyStart);
          item && selectItem(item);
        }
      });

    });

    function selectItem(item) {
      $(item).addClass(focusClass).get(0).focus();
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

    $(this).each(function() {
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
        if(e.keyCode == 27) {
          $(this).siblings('a').trigger('click').focus();
        };
      }); 

      // Click event to show/hide
      $self.on('click', '.toggler', function(e) {
        e.preventDefault();
        e.stopPropagation();
        settings.onOpen.call(this);

        // If I'm an accordion, close the other one
        var $parent = $self.closest('ol, ul');
        if($parent.hasClass('accordion')) {
          var $current = $parent.find('> .current');
          if($current.length && $current.get(0) != $self.get(0)) {
            toggle($current, true);
          }
        }

        // Open or close the item, set the icon, etc.
        toggle($self);
      });

      // The toggler can be initially opened via a data- attribute
      if($self.attr('data-default-state') == 'open') {
        toggle($self);
      }

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
        var openIcon = $tog.attr('data-open-icon') || 'icon-caret-right';
        var closedIcon = $tog.attr('data-closed-icon') || 'icon-caret-down';
        $tog.find('i').attr('class', (getState($li) ? openIcon : closedIcon));
      }

      function getState($li) {
        return $li.attr(closedAttribute);
      }
    });
  };


  /*
    Nice modal provided by Bedrock:  
    https://github.com/mozilla/bedrock/blob/master/media/js/base/mozilla-modal.js

    Modifications made to ensure the modal is more flexible (more than one modal can be on a page, if needed)
  */
  var Modal = (function(w) {
    'use strict';

    var open = false;
    var $modal = null;
    var $body = $('body');
    var options = {};
    var $d = $(w.document);
    var evtNamespace = 'moz-modal';

    var $_contentParent;
    var $_content;

    var closeText = (typeof w.trans == 'undefined') ? 'Close' : w.trans('global-close');

    /*
      origin: element that triggered the modal
      content: content to display in the modal
      options: object of optional params:
        title: title to display at the top of the modal
        onCreate: function to fire after modal has been created
        onDestroy: function to fire after modal has been closed
        allowScroll: boolean - allow/restrict page scrolling when modal is open
    */
    var _createModal = function(origin, content, opts) {
      options = opts;

      // Make sure modal is closed (if one exists)
      if (open) {
        _closeModal();
      }

      // Create new modal
      var title = (options && options.title) ? options.title : '';

      var $modal = $(
          '<div id="modal" role="dialog" ' + (options.classes ? ' class="' + options.classes + '"' : '') + ' aria-labelledby="' + origin.getAttribute('id') + '" tabindex="-1">' +
          '  <div class="window">' +
          '    <div class="inner">' +
          '      <header>' + title + '</header>' +
          '      <div id="modal-close">' +
          '        <a href="#close-modal" class="modal-close-text"> ' + closeText + '</a>' +
          '        <button type="button" class="button">×</button>' +
          '      </div>' +
          '    </div>' +
          '  </div>' +
          '</div>');

      // Add modal to page
      $body.append($modal);

      if (options && !options.allowScroll) {
        $body.addClass('noscroll');
      } else {
        $body.removeClass('noscroll');
      }

      $_content = content;
      $_contentParent = $_content.parent();
      $('#modal .inner').append($_content);
      $_content.addClass('overlay-contents');

      // close modal on clicking close button or background.
      $('#modal-close').click(_closeModal).attr('title', closeText);

      // close modal on clicking the background (but not bubbled event).
      $('#modal .window').click(function (e) {
        if (e.target === this) {
          _closeModal();
        }
      });

      $modal.hide();
      $modal.fadeIn('fast', function() {
        $modal.focus();
      });

      // close with escape key
      $d.on('keyup.' + evtNamespace, function(e) {
        if (e.keyCode === 27 && open) {
          _closeModal();
        }
      });

      // prevent focusing out of modal while open
      $d.on('focus.' + evtNamespace, 'body', function(e) {
        // .contains must be called on the underlying HTML element, not the jQuery object
        if (open && !$modal[0].contains(e.target)) {
          e.stopPropagation();
          $modal.focus();
        }
      });

      // remember which element opened the modal for later focus
      $(origin).addClass('modal-origin');

      open = true;

      // execute (optional) open callback
      if (options && typeof(options.onCreate) === 'function') {
        options.onCreate();
      }
    };

    var _closeModal = function(e) {
      if (e) {
        e.preventDefault();
      }

      $('#modal').fadeOut('fast', function() {
        $_contentParent.append($_content);
        $(this).remove();
      });

      // allow page to scroll again
      $body.removeClass('noscroll');

      // restore focus to element that opened the modal
      $('.modal-origin').focus().removeClass('modal-origin');

      open = false;
      $modal = null;

      // unbind document listeners
      $d.off('.' + evtNamespace);

      // execute (optional) callback
      if (options && typeof(options.onDestroy) === 'function') {
        options.onDestroy();
      }

      // free up options
      options = {};
    };

    return {
      createModal: function(origin, content, opts) {
        _createModal(origin, content, opts);
      },
      closeModal: function() {
        _closeModal();
      }
    };

  })(window);

  // Expose the modal widget as a jQuery plugin
  $.fn.mozModal = function($contentElement, options) {
    return $(this).each(function() {
      Modal.createModal(this, $contentElement, options);
      $contentElement.css('display', 'block');
    });
  };

})(jQuery);
