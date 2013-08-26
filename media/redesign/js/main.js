/*
	INITIALIZE THAT WE HAVE JAVASCRIPT
*/
document.documentElement.className += ' js';

(function($) {

	/*
		Main menu
	*/
	$('#main-nav > ul > li > a').mozMenu();

	/*
		Search animation

		TODO:  What happens on mobile?
	*/
	(function() {
		var $nav = $('#main-nav');
		var $navItems = $nav.find('ul > li:not(:last-child)');
		var $input = $nav.find('.search-wrap input');

		var timeout;
		var createExpander = function(action, delay) {
			return function() {
				timeout && clearTimeout(timeout);
				timeout = setTimeout(function() {
					$nav[action + 'Class']('expand');
				}, delay);
			}
		};

		$input.
			on('focus', createExpander('add', 200)).
			on('blur', createExpander('remove', 600));
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

})(jQuery);