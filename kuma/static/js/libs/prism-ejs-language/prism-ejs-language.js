(function () {
	'use strict';

	if (typeof Prism === 'undefined') {
		console.log('Prism is not defined');
		return false;
	}

	if (!Prism.languages.markup || !Prism.languages.javascript) {
		console.log('prism-ejs-language required markup and javascript languages');
		return false;
	}

	Prism.languages.ejs = Prism.languages.extend('markup', {
		'comment': /(<%%?#)[\s\S]*?([-]?%%?>)/g,
		'punctuation': /(<%%?[-|=|_]?|[-|_]?%%?>|\/?>)/g,
		'entity': /&#?[\da-z]{1,8};/i,
		'attr-name': {
			pattern: /[^\s>\/]+/,
			inside: {
				'namespace': /^[^\s>\/:]+:/,
				'tag': {
					pattern: /<\w+/,
					inside: {
						punctuation: /^</
					}
				},
				'attr-value': {
					pattern: /=(?:("|')(?:\\[\s\S]|(?!\1)[^\\])*\1|[^\s'">=]+)/i,
					inside: {
						'punctuation': [
							/^=/,
							{
								pattern: /(^|[^\\])["']/,
								lookbehind: true
							}
						]
					}
				},
				'punctuation': /=/
			}
		}
	});

	Prism.languages.insertBefore('ejs', 'tag', {
		script: {
			pattern: /(<%%?[-|=|_]?)[\s\S]*?(?=[-|_]?%%?>)/i,
			lookbehind: !0,
			inside: Prism.languages.javascript,
			alias: 'language-javascript'
		}
	});
}());
