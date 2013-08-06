/*
	INITIALIZE THAT WE HAVE JAVASCRIPT
*/
document.documentElement.className += ' js';

(function($) {

	/*
		MAIN MENU
	*/
	(function() {
		var showDelay = hideDelay = 500;  // Milliseconds
		var closeTimeout;
		var showTimeout;
		var $openMenu;
		var $menuItems = $('nav > ul > li > a');

		$menuItems.each(function() {
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
				}, showDelay);
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
			}, hideDelay);
		}
	})();

	/*
		Search animation

		TODO:  What happens on mobile?
	*/
	(function() {
		var $navItems = $('header nav > ul > li:not(:last-child)');
		var $input = $('header .search-wrap input');
		var width = $input.width();
		var fadeDuration = 100;
		var growDuration = 200;

		$input.
			on('focus', function() {
				$navItems.fadeOut(fadeDuration, function() {
					$input.animate({ width: $input.attr('data-grow') }, growDuration);
				});
			}).
			on('blur', function() {
				$input.animate({ width: width }, {
					duration: growDuration,
					complete: function() {
						$navItems.fadeIn(fadeDuration);
					}
				});
			});
	})();


	/*
		Togglers within articles, TOC for example
	*/
	$('.toggleable').each(function() {
		var $self = $(this);
		var $container = $self.find('.toggle-container');
		var $toggler = $self.find('.toggler');
		var closedAttribute = 'data-closed';

		// Initialize open / close for the purpose of animation
		if($self.hasClass('closed')) {
			$self.attr(closedAttribute, 'true').removeClass('closed');
			$container.hide();
		}
		setIcon();

		// Click event to show/hide
		$self.on('click', '.toggler', function(e) {
			e.preventDefault();
			e.stopPropagation();

			if(getState()) {
				$self.attr(closedAttribute, '');
				$container.slideDown();
			}
			else {
				$self.attr(closedAttribute, 'true');
				$container.slideUp();
			}
			setIcon();
		});

		function setIcon() {
			$toggler.find('i').attr('class', 'icon-caret-'  + (getState() ? 'up' : 'down'));
		}

		function getState() {
			return $self.attr(closedAttribute);
		}
	});


	/* 
		Toggle for quick links show/hide
	*/
	(function() {
		var side = $('#quick-links-toggle').closest('.wiki-column').attr('id');
		// Quick Link toggles
		$('#quick-links-toggle, #show-quick-links').on('click', function(e) {
			e.preventDefault();
			$('#' + side).toggleClass('column-closed');
			$('#wiki-column-container').toggleClass(side + '-closed');
			$('#wiki-controls .quick-links').toggleClass('hidden');
		});
	})();

})(jQuery);