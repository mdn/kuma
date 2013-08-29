(function($) {

  /*
    Plugin to create nav menus, show/hide delays, etc.
    Accessible by keyboard too!
  */
  $.fn.mozMenu = function(options) {

    var settings = $.extend({
      showDelay: 500,
      hideDelay: 500,
      submenu: null,
      focusOnOpen: true,
      brickOnClick: false,
      onOpen: function(){},
      onClose: function() {}
    }, options);

    var closeTimeout;
    var showTimeout;

    $(this).each(function() {
      var $self = $(this);
      var $li = $self.parent();
      var initialized;

      // Brick on click?
      if(settings.brickOnClick) {
        $self.on('click', function(e) {
          e.preventDefault();
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
          $submenu.addClass('open').fadeIn();

          // Find the first link for improved usability
          if(settings.focusOnOpen) {
            var firstLink = $submenu.find('a');
            try { // Putting in try/catch because of opacity/focus issues in IE
              firstLink.length && firstLink[0].focus();
            }
            catch(e){}
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
        $sub && $sub.removeClass('open').fadeOut(); 
        settings.onClose();
      }, settings.hideDelay);
    }
  };

})(jQuery);