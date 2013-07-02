(function($) {
	$.each({{ flags|safe }}, function() {
		try {
			var json = $.parseJSON(this.note);
			if(json.selector) {
				$(json.selector).
					attr('data-waffle-message', json.message || gettext('BETA: Only available to testers')).
					addClass('waffle-beta');
			}
		}
		catch(e){}
	});
})(jQuery);