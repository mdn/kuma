Prism.languages.javascript = Prism.languages.extend('clike', {
	'keyword': /\b(var|let|if|else|while|do|for|return|in|instanceof|function|new|with|typeof|try|catch|finally|null|break|continue)\b/g,
	'number': /\b-?(0x[\dA-Fa-f]+|\d*\.?\d+([Ee]-?\d+)?|NaN|-?Infinity)\b/g
});

Prism.languages.insertBefore('javascript', 'keyword', {
	'regex': {
		pattern: /(^|[^/])\/(?!\/)(\[.+?]|\\.|[^/\r\n])+\/[gim]{0,3}(?=\s*($|[\r\n,.;})]))/g,
		lookbehind: true
	}
});

if (Prism.languages.markup) {
	Prism.languages.insertBefore('markup', 'tag', {
		'script': {
			pattern: /(&lt;|<)script[\w\W]*?(>|&gt;)[\w\W]*?(&lt;|<)\/script(>|&gt;)/ig,
			inside: {
				'tag': {
					pattern: /(&lt;|<)script[\w\W]*?(>|&gt;)|(&lt;|<)\/script(>|&gt;)/ig,
					inside: Prism.languages.markup.tag.inside
				},
				rest: Prism.languages.javascript
			}
		}
	});
}