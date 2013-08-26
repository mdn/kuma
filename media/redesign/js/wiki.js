(function($) {

	// Settings menu
	$('#settings-menu').mozMenu();

	// New tag placeholder
	// Has to be placed in ready call because the plugin is initialized in one
	$.ready(function() {
		$('.tagit-new input').attr('placeholder', gettext('New tag...'));
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