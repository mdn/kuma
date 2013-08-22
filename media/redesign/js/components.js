(function($) {

	/*
		Plugin to create nav menus, show/hide delays, etc.
		Accessible by keyboard too!
	*/
	$.fn.mozMenu = function(options) {

		var settings = $.extend({
			showDelay: 500,
			hideDelay: 500
		}, options);

		var closeTimeout;
		var showTimeout;
		var $openMenu;

		$(this).each(function() {
			var $self = $(this);
			var $li = $self.parent();
			var initialized;

			// Find a submenu.  If one doesn't exist, no need to go further
			var $submenu = $li.find('.submenu');
			
			// Add a mouseenter / focus event to get the showing of the submenu in motion
			$self.on('mouseenter focus', function() {
				// If no submenu, go
				if(!$submenu.length) {
					clear(showTimeout);
					$openMenu && closeSubmenu($openMenu.parent().find('.submenu'));
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
				}

				// If there's an open submenu and it's not this one, close it
				// Used for tab navigation from submenu to the next menu item
				if($openMenu && $openMenu != $self) {
					clear(showTimeout);
					closeSubmenu($openMenu.parent().find('.submenu'));
				}
				else if($openMenu == $self) {
					clear(closeTimeout);
				}

				// Show my submenu after the showDelay
				$openMenu = $self;
				showTimeout = setTimeout(function() {
					$submenu.addClass('open').fadeIn();
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
			}, settings.hideDelay);
		}
	};



})(jQuery);