/* jshint browser:true */

var scrollbackAdded = false;

function addScrollback(roomName, suggestedNick) {
	var div = document.createElement('div');
	if (!roomName) {
		return;
	}
	if (!scrollbackAdded) {
		window.scrollback = {
			"room": roomName,
			"form": "toast",
			"minimize": false,
			"titlebarColor": "#00539f"
		};
		if(suggestedNick) {
			window.scrollback.nick = suggestedNick;
		} else {
			window.scrollback.nick = "guest";
		}
		var el = document.createElement("script");
		el.async = 1;
		el.src = (location.protocol === "https:" ? "https:" : "http:") + "//scrollback.io/client.min.js";
		document.getElementsByTagName("script")[0].parentNode.appendChild(el);
		scrollbackAdded = true;
	} else {
		var iframe = document.getElementsByClassName("scrollback-stream")[0];
		iframe.src = iframe.src.replace(/\/[^/]*\?/, '/' + encodeURIComponent(roomName) + '?');
	}
}