(function($) {

  var focusClass = 'focused';

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
      onOpen: function(){},
      onClose: function() {}
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
          $self.on('mouseleave', function() {
            clear(showTimeout);
            closeSubmenu($submenu);
          });

          // Hide the submenu when the submenu is blurred for hideDelay
          $submenu.on('mouseleave', function() {
            clear(showTimeout);
            closeSubmenu($submenu);
          });

          // Cancel the close timeout if moving from main menu item to submenu
          $submenu.on('mouseenter', function() {
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
            else if(e.keyCode == 9) { // Tab
              if(e.target == $submenu.find('a').last().get(0)) {
                closeSubmenu($submenu);
              }
            }
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
          $submenu.addClass('open').attr('aria-hidden', 'false').fadeIn();

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
        $sub && $sub.removeClass('open').attr('aria-hidden', 'true').fadeOut();
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
      items: null
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

      // Click event to show/hide
      $self.on('click', '.toggler', function(e) {
        e.preventDefault();
        e.stopPropagation();

        // If I'm an accordion, close the other one
        var $parent = $self.closest('ol, ul');
        if($parent.hasClass('accordion')) {
          var $current = $parent.find('> .current');
          if($current.length && $current.get(0) != $self.get(0)) {
            toggle($current, true);
          }
        }

        // Handle me
        toggle($self);
      });

      function toggle($li, forceClose) {
        var pieces = getTogglerComponents($li);

        if(!getState($li) || forceClose) {
          $li.attr(closedAttribute, 'true').removeClass('current');
          pieces.$container.slideUp();
        }
        else {
          $li.attr(closedAttribute, '').addClass('current');
          pieces.$container.slideDown();
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

})(jQuery);
