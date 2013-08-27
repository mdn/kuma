(function($) {

	// Settings menu
	$('#settings-menu').mozMenu();

	// New tag placeholder
	// Has to be placed in ready call because the plugin is initialized in one
	$.ready(function() {
		$('.tagit-new input').attr('placeholder', gettext('New tag...'));
	});

	// "From Search" submenu click
	$('.from-search-navigate').mozMenu({
		submenu: $('.from-search-toc'),
		brickOnClick: true
	});


})(jQuery);