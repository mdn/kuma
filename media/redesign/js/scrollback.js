/* jshint browser:true */
var scrollbackAdded = false;

function addScrollback(roomName, suggestedNick) {
	if (!roomName) {
		return;
	}
	if (!scrollbackAdded) {
		window.scrollback = {
			"room": roomName,
			"form": "toast",
			"minimize": false,
			"nick": suggestedNick,
			"titlebarColor": "#00539f"
		};
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