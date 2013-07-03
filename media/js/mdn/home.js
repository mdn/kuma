/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

$(document).ready(function(){
	// corrects some weirdness with the slide show bogarting focus and breaking keyboard tabbing through links
	$("#slide-control a").focus(function(){ window.focus(this); }); 

	// Create any tabbed interface as necessary
	$(".tabbed").each(function(index) {
		new TabInterface(this, index);
	});
});