(function($) {

	// New tag placeholder
	// Has to be placed in ready call because the plugin is initialized in one
	$.ready(function() {
		$('.tagit-new input').attr('placeholder', gettext('New tag...'));
	});

})(jQuery);