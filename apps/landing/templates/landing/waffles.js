(function($) {
	var waffles = window.mdn.waffles = {};
	$.each({{ flags|safe }}, function() {
		waffles[this.name] = 1;
		try {
			var json = $.parseJSON(this.note);
			var selector = json.selector;
			if(selector) {
				$(selector).
					attr('data-waffle-message', json.message || gettext('BETA: Only available to testers')).
					addClass('waffle-beta');
			}
		}
		catch(e){}
	});
})(jQuery);