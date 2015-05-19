/* global document, window, setTimeout*/
/* exported addScrollback */

var scrollbackAdded = false;
var scrollbackWarningShowed = false;
var host = "scrollback.io";
function showNotice() {
    "use strict";
	/* displays a notice that the widget is not a substitute for tech support */
	if(!scrollbackWarningShowed) {
		scrollbackWarningShowed = true;

        var noticeOverlay = document.createElement("div");
        var noticeDiv = document.createElement("div");
        var okayButton = document.createElement("button");
        var pTag = document.createElement("p");
        var guidelinesLink = document.createElement("a");
        var privacyLink = document.createElement("a");

        guidelinesLink.href = "https://developer.mozilla.org/en-US/docs/Mozilla/QA/Getting_Started_with_IRC";
        guidelinesLink.setAttribute("target", "_blank");
		guidelinesLink.appendChild(document.createTextNode("guidelines"));
        privacyLink.href = "http://web.scrollback.io/privacy/";
        privacyLink.setAttribute("target", "_blank");
		privacyLink.appendChild(document.createTextNode("Privacy Policy"));
		guidelinesLink.style.color = privacyLink.style.color = "#000000";
		guidelinesLink.style.textDecoration = privacyLink.style.textDecoration = "underline";


		pTag.appendChild(document.createTextNode("This is a community chat room, please follow the "));
		pTag.appendChild(guidelinesLink);
		pTag.appendChild(document.createTextNode("."));
        pTag.appendChild(document.createTextNode(" This public chat is provided by Scrollback and is subject to its "));
		pTag.appendChild(privacyLink);
		pTag.appendChild(document.createTextNode("."));


        noticeOverlay.className += " scrollback-stream scrollback-toast";
        okayButton.innerText = okayButton.textContent = "Okay";
		var okayButtonStyle = "-webkit-appearance: none;  -moz-appearance: none;  appearance: none;  -webkit-transition: 0.3s ease;  transition: 0.3s ease;  background-color: rgb(51, 204, 170);  background-image: none;  border-radius: 2px;  color: rgb(255, 255, 255);  cursor: pointer;  display: inline-block;  font-size: 13px;  font-weight: bold;  padding: .75em 1em;  text-transform: uppercase;width:100%;border-bottom:0;";

		okayButton.setAttribute("style", okayButtonStyle);
		okayButton.onclick = function() {
			noticeOverlay.parentNode.removeChild(noticeOverlay);
		};
        noticeDiv.appendChild(pTag);
        noticeDiv.appendChild(okayButton);
        noticeDiv.setAttribute("style", "line-height: 1.625;padding: 1.5em; text-align:center;width:100%;position:absolute; bottom:0;left:0;box-sizing: border-box;background-color:white;");
        noticeOverlay.setAttribute("style", "  background-color: rgba(0,0,0,.6); box-sizing: border-box;z-index:1000");
        noticeOverlay.appendChild(noticeDiv);
		document.body.appendChild(noticeOverlay);
	}
}

function addScrollback(roomName, suggestedNick) {
    "use strict";
	if (!roomName) {
		return;
	}
	if (!scrollbackAdded) {
		window.scrollback = {
			"room": roomName,
			"form": "toast",
			"titlebarColor": "#00539f",
            minimize: false
		};
		if(suggestedNick) {
			window.scrollback.nick = suggestedNick;
		} else {
			window.scrollback.nick = "guest";
		}
		var el = document.createElement("script");
		el.async = 1;
		el.src = "https://" + host + "/client.min.js";
		document.getElementsByTagName("script")[0].parentNode.appendChild(el);
		scrollbackAdded = true;
        el.onload = function(){
            setTimeout(showNotice, 100);
        };
	} else {
		var iframe = document.getElementsByClassName("scrollback-stream")[0];
		var url = iframe.src;
		url = url.replace("https://" + host, "");
		url = "https://" + host + url.replace(/\/[^/]*/, "/" + roomName);
		iframe.src = url;
	}
}
