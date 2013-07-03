/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

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