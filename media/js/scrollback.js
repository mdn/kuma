/* jshint browser:true, multistr:true */
/* jshint strict: false */
/* exported addScrollback */

var scrollbackAdded = false;
var scrollbackWarningShowed = false;
var host = 'scrollback.io';
function showNotice() {
	/* displays a notice that the widget is not a substitute for tech support */
	if(!scrollbackWarningShowed) {
		scrollbackWarningShowed = true;

		/* compute position of the scrollback widget relative to the window and place the notice over it */
		var scrollbackEl = document.getElementsByClassName('scrollback-stream')[0];
		var scrollbackStyle = window.getComputedStyle(scrollbackEl);

		var noticeText = "Welcome to the Mozilla IRC network. Please follow the "+
		"<a href=>"+
		"general rules and etiquette</a> of this community.";

		var noticeDiv = document.createElement('div');
		var link = document.createElement('a');

		link.href = 'https://developer.mozilla.org/en-US/docs/Mozilla/QA/Getting_Started_with_IRC';
		link.appendChild(document.createTextNode("general rules and etiquette"));
		link.style.color = '#000000';
		link.style.textDecoration = 'underline';

		noticeDiv.appendChild(document.createTextNode("Welcome to Mozilla's IRC network. Please follow the "));
		noticeDiv.appendChild(link);
		noticeDiv.appendChild(document.createTextNode(" of this community."));

		['position', 'bottom', 'left', 'right'].forEach(function (prop) {
			noticeDiv.style[prop] = scrollbackStyle[prop];
		});

		noticeDiv.style.boxSizing = 'border-box';
		noticeDiv.style.zIndex = 1000;
		noticeDiv.style.padding = '8px';
		noticeDiv.style.backgroundColor = '#33ccaa';
		noticeDiv.style.color = '#333333';
		noticeDiv.style.boxShadow = '0 4px 16px 0 rgba(0,0,0,0.5)'
		noticeDiv.style.width = parseInt(scrollbackStyle.width) + 2*parseInt(scrollbackStyle.borderWidth) + 'px';

		var closeButton = document.createElement('button');
		closeButton.innerHTML = "Okay";
		var closeButtonStyle = 'display: block; margin: 0 auto; cursor: pointer; color: white; padding: 0;' +
			'line-height: 40px; text-align: center; border: none; background: #226655; margin-top: 8px; width: 100%';

		closeButton.setAttribute('style', closeButtonStyle);
		closeButton.onclick = function() {
			noticeDiv.remove();
		}

		noticeDiv.appendChild(closeButton);

		document.body.appendChild(noticeDiv);
	}
}

function addScrollback(roomName, suggestedNick) {
	if (!roomName) {
		return;
	}
	if (!scrollbackAdded) {
		window.scrollback = {
			"room": roomName,
			"form": "toast",
			"minimize": true,
			"titlebarColor": "#00539f"
		};
		if(suggestedNick) {
			window.scrollback.nick = suggestedNick;
		} else {
			window.scrollback.nick = "guest";
		}
		var el = document.createElement("script");
		el.async = 1;
		el.src = 'https://' + host + '/client.min.js';
		document.getElementsByTagName("script")[0].parentNode.appendChild(el);
		scrollbackAdded = true;
		setTimeout(showNotice, 2000);
	} else {
		var iframe = document.getElementsByClassName("scrollback-stream")[0];
		var url = iframe.src;
		url = url.replace('https://' + host, '');
		url = 'https://' + host + url.replace(/\/[^/]*/, '/' + roomName);
        console.log(url);
		iframe.src = url;
	}
}
