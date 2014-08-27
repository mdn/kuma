function PromoteMDN(userSettings) {

    // For the time being, we are not gonna do anything if querySelectorAll is not available in the browser
    if (!'querySelectorAll' in document) {
        return;
    }

    var defaults = {
        searchElements: ['p', 'div', 'span'],
        trackingString: '?utm_source=js%20snippet&utm_medium=content%20link&utm_campaign=promote%20mdn',
        maxLinks: 3,
        linkClass: '',
        extraLinks: {}
    };

    var mdnRoot = 'https://developer.mozilla.org/docs/';

    var dataset = {
        'JavaScript': mdnRoot + 'JavaScript',
        'JS Reference': mdnRoot + 'JavaScript',
        'JS Documentation': mdnRoot + 'JavaScript',
        'JS': mdnRoot + 'JavaScript',
        'HTML5': 'https://developer.mozilla.org/html5',
        'JS Array': mdnRoot + 'JavaScript/Reference/Global_Objects/Array',
        'JS Function': mdnRoot + 'JavaScript/Reference/Global_Objects/Function',
        'JS Number': mdnRoot + 'JavaScript/Reference/Global_Objects/Number',
        'JS RegExp': mdnRoot + 'JavaScript/Reference/Global_Objects/RegExp',
        'JS String': mdnRoot + 'JavaScript/Reference/Global_Objects/String',
        'JS Tutorial': mdnRoot + 'JavaScript/Guide',
        'Learn JavaScript': mdnRoot + 'JavaScript/Guide',
        'Learn JS': mdnRoot + 'JavaScript/Guide',
        'DOM': mdnRoot + 'DOM',
        'WebGL': mdnRoot + 'WebGL',
        'WebSockets': mdnRoot + 'WebSockets',
        'WebSocket': mdnRoot + 'WebSockets',
        'JSON': mdnRoot + 'JSON',
        'XUL': mdnRoot + 'XUL',
        'HTML': mdnRoot + 'Web/HTML',
        'CSS Reference': mdnRoot + 'Web/CSS/CSS_Reference',
        'CSS': mdnRoot + 'Web/CSS',
        'CSS3': mdnRoot + 'Web/CSS/CSS3',
        'CSS Transitions': mdnRoot + 'Web/CSS/Using_CSS_transitions',
        'CSS3 Transitions': mdnRoot + 'Web/CSS/Using_CSS_transitions',
        'CSS Gradients': mdnRoot + 'Web/CSS/Using_CSS_transitions',
        'CSS3 Gradients': mdnRoot + 'Web/CSS/Using_CSS_transitions',
        'linear-gradient': mdnRoot + 'Web/CSS/linear-gradient',
        'radial-gradient': mdnRoot + 'Web/CSS/linear-gradient',
        'repeating-linear-gradient': mdnRoot + 'Web/CSS/repeating-linear-gradient',
        'repeating-radial-gradient': mdnRoot + 'Web/CSS/repeating-radial-gradient',
        'CSS Animation': mdnRoot + 'Web/CSS/Using_CSS_animations',
        'CSS3 Animation': mdnRoot + 'Web/CSS/Using_CSS_animations',
        'CSS Transform': mdnRoot + 'Web/CSS/Using_CSS_transform',
        'CSS3 Transform': mdnRoot + 'Web/CSS/Using_CSS_transform',
        'CSS 3D Transform': mdnRoot + 'Web/CSS/Using_CSS_transform',
        'border-image': mdnRoot + 'Web/CSS/border-image',
        'border-image-source': mdnRoot + 'Web/CSS/border-image-source',
        'border-image-repeat': mdnRoot + 'Web/CSS/border-image-repeat',
        'border-image-width': mdnRoot + 'Web/CSS/border-image-width',
        'border-image-outset': mdnRoot + 'Web/CSS/border-image-outset',
        'CSS Flexbox': 'https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_flexible_boxes',
        'flexbox': 'https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_flexible_boxes',
        'flexible box': 'https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_flexible_boxes',
        'Media queries': mdnRoot + 'Web/CSS/Media_queries',
        'pseudo-class': mdnRoot + 'Web/CSS/pseudo-classes',
        'pseudo-classes': mdnRoot + 'Web/CSS/pseudo-classes',
        'pseudo-element': mdnRoot + 'Web/CSS/Pseudo-elements',
        'at-rule': mdnRoot + 'Web/CSS/At-rule',
        '@-rule': mdnRoot + 'Web/CSS/At-rule',
        'MDN': 'https://developer.mozilla.org/',
        'Mozilla Developer Network': 'https://developer.mozilla.org/',
        'devmo': 'https://developer.mozilla.org/',
        'Kuma': mdnRoot + 'Project:Getting_started_with_Kuma',
        'KumaScript': mdnRoot + 'Project:Introduction_to_KumaScript',
        'B2G': mdnRoot + 'Mozilla/Firefox_OS',
        'Firefox OS': mdnRoot + 'Mozilla/Firefox_OS',
        'Boot to Gecko': mdnRoot + 'Mozilla/Firefox_OS',
        'Persona': 'https://developer.mozilla.org/Persona',
        'BrowserID': 'https://developer.mozilla.org/Persona',
        'IndexedDB': mdnRoot + 'IndexedDB',
        'Vibration API': mdnRoot + 'WebAPI/Vibration',
        'Geolocation': mdnRoot + 'Using_geolocation',
        'SVG': mdnRoot + 'SVG',
        'ARIA': mdnRoot + 'Accessibility/ARIA',
        'WebRTC': mdnRoot + 'WebRTC',
        'WebAPI': mdnRoot + 'WebAPI',
        'Web apps': mdnRoot + 'Apps',
        'Emscripten': mdnRoot + 'Emscripten',
        'L20n': mdnRoot + 'L20n',
        'Firefox Marketplace': 'https://developer.mozilla.org/Marketplace',
        'Gecko': mdnRoot + 'Mozilla/Gecko',
        'XPCOM': mdnRoot + 'Mozilla/XPCOM',
        '#mdn': 'irc://irc.mozilla.org/mdn',
        '#mdndev': 'irc://irc.mozilla.org/mdndev',
        'mozilla-central': 'https://developer.mozilla.org/en-US/docs/mozilla-central',
        'Mozilla': 'https://www.mozilla.org/'
    };

    options = extend(defaults, userSettings || {});
    dataset = extend(dataset, options.extraLinks);

    var replaceCount = 0,
        linkRegex = /<a[^>]*>(.*?)<\/a>/,
        linkGlobalMatchRegex = new RegExp(linkRegex + 'g'),
        linkReplaceMatchRegex = new RegExp(linkRegex);

    var elements = document.querySelectorAll(options.searchElements.join(', '));

    forEach(elements, function(o){
        var text = o.innerHTML,
            placeholder,
            placeholderIndex = 0,
            anchorsExisting = [],
            anchorsNew = [];

        var match = text.match(linkGlobalMatchRegex);
        if (match && match.length) {
            for(var i = 0; i < match.length; i++) {
                var anchor = linkReplaceMatchRegex.exec(text);
                placeholder = getPlaceholder(placeholderIndex);
                anchorsExisting[placeholder] = anchor[0];
                text = text.replace(linkReplaceMatchRegex, placeholder);
                placeholderIndex++;
            }
        }

        // text is now stripped of all hyperlinks
        for(var keyword in dataset) {
            var keywordRegex = new RegExp(' ' + keyword + ' ', 'i');

            if (replaceCount < options.maxLinks) {
                if (text.match(keywordRegex)) {
                    var exactWord = keywordRegex.exec(text);
                    exactWord = exactWord[0].trim();
                    var link = '<a href="'+ dataset[keyword] + options.trackingString +'" class="'+ options.linkClass
                        +'">' + exactWord + '</a>';
                    placeholder = getPlaceholder(placeholderIndex);
                    placeholderIndex++;
                    text = text.replace(exactWord, placeholder);
                    anchorsNew[placeholder] = link;
                    delete dataset[keyword];
                    replaceCount++;
                }
            } else {
                break;
            }
        }

        // Now let's replace placeholders with actual anchor tags, pre-existed ones and new ones.
        for(var l in anchorsExisting) {
            text = text.replace(l, anchorsExisting[l]);
        }

        for(var l in anchorsNew) {
            text = text.replace(l, ' ' + anchorsNew[l] + ' ');
        }

        o.innerHTML = text;
    });

    function forEach(arr, callback) {
        if(Array.prototype.forEach) {
            Array.prototype.forEach.call(arr, callback);
        }
        else { // Shim for older browsers that doesn't have array.forEach
            if (typeof callback !== 'function') {
                throw new TypeError();
            }

            var len = arr.length >>> 0;
            var thisArg = arguments.length >= 2 ? arguments[1] : void 0;
            for(var i = 0; i < len; i++) {
                if (i in arr) {
                    callback.call(thisArg, arr[i], i, arr);
                }
            }
        }
    }

    function extend(out) {
        out = out || {};

        for(var i = 1; i < arguments.length; i++) {
            if (!arguments[i])
                continue;

            for(var key in arguments[i]) {
                if (arguments[i].hasOwnProperty(key))
                    out[key] = arguments[i][key];
            }
        }

        return out;
    };

    function getPlaceholder(placeholderIndex) {
        return '{_m$d$n_repl$ace_' + placeholderIndex + '_}';
    }
};
