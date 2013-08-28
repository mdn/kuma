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
		Togglers within articles, TOC, accordion subnav, etc. for example
	*/
	$('.toggleable').each(function() {
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
				$container: $li.find('.toggle-container'),
				$toggler: $li.find('> .toggler')
			};
		}

		function setIcon($tog, $li) {
			$tog.find('i').attr('class', 'icon-caret-'  + (getState($li) ? 'up' : 'down'));
		}

		function getState($li) {
			return $li.attr(closedAttribute);
		}
	});

	/*
		Persona Login
	*/
	$('.persona-login').click(function(e) {
		if(!$(this).hasClass('toggle')) {
			navigator.id.get(function(assertion) {
				if(!assertion) return;
				$('input[name="assertion"]').val(assertion.toString());
				$('form.browserid').first().submit();
			});
			return false;
		}
	});

})(jQuery);