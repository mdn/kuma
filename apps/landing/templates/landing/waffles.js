(function($) {

	var flags = {{ flags|safe }};

	if(flags.length) {
		$.each(flags, function() {
			try {
				var json = $.parseJSON(this.note);
				if(json.selector) {
					$(json.selector).
						attr('data-waffle-message', json.message || gettext('BETA: Only available to beta testers')).
						addClass('waffle-beta');
				}
			}
			catch(e){}
		});
	}

})(jQuery);