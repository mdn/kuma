function PromoteMDNLinks(userSettings) {

    // For the time being, we are not gonna do anything if querySelectorAll is not available in the browser
    if (!'querySelectorAll' in document) {
        return;
    }

    var dataset = {
        'JavaScript': 'https://developer.mozilla.org/docs/JavaScript',
        'JS Reference': 'https://developer.mozilla.org/docs/JavaScript',
        'JS Documentation': 'https://developer.mozilla.org/docs/JavaScript',
        'JS': 'https://developer.mozilla.org/docs/JavaScript',
        'HTML5': 'https://developer.mozilla.org/html5',
        'JS Array': 'https://developer.mozilla.org/docs/JavaScript/Reference/Global_Objects/Array',
        'JS Function': 'https://developer.mozilla.org/docs/JavaScript/Reference/Global_Objects/Function',
        'JS Number': 'https://developer.mozilla.org/docs/JavaScript/Reference/Global_Objects/Number',
        'JS RegExp': 'https://developer.mozilla.org/docs/JavaScript/Reference/Global_Objects/RegExp',
        'JS String': 'https://developer.mozilla.org/docs/JavaScript/Reference/Global_Objects/String',
        'JS Tutorial': 'https://developer.mozilla.org/docs/JavaScript/Guide',
        'Learn JavaScript': 'https://developer.mozilla.org/docs/JavaScript/Guide',
        'Learn JS': 'https://developer.mozilla.org/docs/JavaScript/Guide',
        'DOM': 'https://developer.mozilla.org/docs/DOM',
        'WebGL': 'https://developer.mozilla.org/docs/WebGL',
        'WebSockets': 'https://developer.mozilla.org/docs/WebSockets',
        'WebSocket': 'https://developer.mozilla.org/docs/WebSockets',
        'JSON': 'https://developer.mozilla.org/docs/JSON',
        'XUL': 'https://developer.mozilla.org/docs/XUL',
        'HTML': 'https://developer.mozilla.org/docs/Web/HTML',
        'CSS Reference': 'https://developer.mozilla.org/docs/Web/CSS/CSS_Reference',
        'CSS': 'https://developer.mozilla.org/docs/Web/CSS',
        'CSS3': 'https://developer.mozilla.org/docs/Web/CSS/CSS3',
        'CSS Transitions': 'https://developer.mozilla.org/docs/Web/CSS/Using_CSS_transitions',
        'CSS3 Transitions': 'https://developer.mozilla.org/docs/Web/CSS/Using_CSS_transitions',
        'CSS Gradients': 'https://developer.mozilla.org/docs/Web/CSS/Using_CSS_transitions',
        'CSS3 Gradients': 'https://developer.mozilla.org/docs/Web/CSS/Using_CSS_transitions',
        'linear-gradient': 'https://developer.mozilla.org/docs/Web/CSS/linear-gradient',
        'radial-gradient': 'https://developer.mozilla.org/docs/Web/CSS/linear-gradient',
        'repeating-linear-gradient': 'https://developer.mozilla.org/docs/Web/CSS/repeating-linear-gradient',
        'repeating-radial-gradient': 'https://developer.mozilla.org/docs/Web/CSS/repeating-radial-gradient',
        'CSS Animation': 'https://developer.mozilla.org/docs/Web/CSS/Using_CSS_animations',
        'CSS3 Animation': 'https://developer.mozilla.org/docs/Web/CSS/Using_CSS_animations',
        'CSS Transform': 'https://developer.mozilla.org/docs/Web/CSS/Using_CSS_transform',
        'CSS3 Transform': 'https://developer.mozilla.org/docs/Web/CSS/Using_CSS_transform',
        'CSS 3D Transform': 'https://developer.mozilla.org/docs/Web/CSS/Using_CSS_transform',
        'border-image': 'https://developer.mozilla.org/docs/Web/CSS/border-image',
        'border-image-source': 'https://developer.mozilla.org/docs/Web/CSS/border-image-source',
        'border-image-repeat': 'https://developer.mozilla.org/docs/Web/CSS/border-image-repeat',
        'border-image-width': 'https://developer.mozilla.org/docs/Web/CSS/border-image-width',
        'border-image-outset': 'https://developer.mozilla.org/docs/Web/CSS/border-image-outset',
        'CSS Flexbox': 'https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_flexible_boxes',
        'flexbox': 'https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_flexible_boxes',
        'flexible box': 'https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_flexible_boxes',
        'Media queries': 'https://developer.mozilla.org/docs/Web/CSS/Media_queries',
        'pseudo-class': 'https://developer.mozilla.org/docs/Web/CSS/pseudo-classes',
        'pseudo-classes': 'https://developer.mozilla.org/docs/Web/CSS/pseudo-classes',
        'pseudo-element': 'https://developer.mozilla.org/docs/Web/CSS/Pseudo-elements',
        'at-rule': 'https://developer.mozilla.org/docs/Web/CSS/At-rule',
        '@-rule': 'https://developer.mozilla.org/docs/Web/CSS/At-rule',
        'MDN': 'https://developer.mozilla.org/',
        'Mozilla Developer Network': 'https://developer.mozilla.org/',
        'devmo': 'https://developer.mozilla.org/',
        'Kuma': 'https://developer.mozilla.org/docs/Project:Getting_started_with_Kuma',
        'KumaScript': 'https://developer.mozilla.org/docs/Project:Introduction_to_KumaScript',
        'B2G': 'https://developer.mozilla.org/docs/Mozilla/Firefox_OS',
        'Firefox OS': 'https://developer.mozilla.org/docs/Mozilla/Firefox_OS',
        'Boot to Gecko': 'https://developer.mozilla.org/docs/Mozilla/Firefox_OS',
        'Persona': 'https://developer.mozilla.org/Persona',
        'BrowserID': 'https://developer.mozilla.org/Persona',
        'IndexedDB': 'https://developer.mozilla.org/docs/IndexedDB',
        'Vibration API': 'https://developer.mozilla.org/docs/WebAPI/Vibration',
        'Geolocation': 'https://developer.mozilla.org/docs/Using_geolocation',
        'SVG': 'https://developer.mozilla.org/docs/SVG',
        'ARIA': 'https://developer.mozilla.org/docs/Accessibility/ARIA',
        'WebRTC': 'https://developer.mozilla.org/docs/WebRTC',
        'WebAPI': 'https://developer.mozilla.org/docs/WebAPI',
        'Web apps': 'https://developer.mozilla.org/docs/Apps',
        'Mozilla Developer Program': 'https://developer.mozilla.org/docs/Mozilla/Developer_Program',
        'Emscripten': 'https://developer.mozilla.org/docs/Emscripten',
        'L20n': 'https://developer.mozilla.org/docs/L20n',
        'Firefox Marketplace': 'https://developer.mozilla.org/Marketplace',
        'Gecko': 'https://developer.mozilla.org/docs/Mozilla/Gecko',
        'XPCOM': 'https://developer.mozilla.org/docs/Mozilla/XPCOM',
        '#mdn': 'irc://irc.mozilla.org/mdn',
        '#mdndev': 'irc://irc.mozilla.org/mdndev',
        'mozilla-central': 'https://developer.mozilla.org/en-US/docs/mozilla-central',
        'Mozilla': 'https://www.mozilla.org/'
    };

    var options = {
        includeElems: ['p', 'div', 'span'],
        trackingString: '?utm_source=js%20snippet&utm_medium=content%20link&utm_campaign=promote%20mdn',
        maxLinks: 3,
        linkClass: ''
    };

    options = extend({}, options, userSettings || {});
    dataset = extend({}, dataset, options.extraLinks || {})

    var replaceCount = 0;
    var re = new RegExp(/<a[^>]*>(.*?)<\/a>/);

    var elements = document.querySelectorAll(options.includeElems.join(', '));
    forEach(elements, function(o){
        var text = o.innerHTML;
        var placeholder;
        var placeholderIndex = 0;
        var anchors_existing = [];
        var anchors_new = [];

        if (text.match(/<a[^>]*>(.*?)<\/a>/g) && text.match(/<a[^>]*>(.*?)<\/a>/g).length) {
            var anchorCount = text.match(/<a[^>]*>(.*?)<\/a>/g).length;

            for (var i = 0; i < anchorCount; i++) {
                var anchor = re.exec(text);
                placeholder = '{_m$d$n_repl$ace_' + placeholderIndex + '_}';
                anchors_existing[placeholder] = anchor[0];
                text = text.replace(re, placeholder);
                placeholderIndex++;
            }
        }

        // text is now stripped of all hyperlinks
        for (var keyword in dataset) {
            var keywordRegex = new RegExp(' ' + keyword + ' ', 'i');

            if (replaceCount <= options.maxLinks) {
                if (text.match(keywordRegex)) {
                    var exactWord = keywordRegex.exec(text);
                    exactWord = exactWord[0].trim();
                    var link = '<a href="'+ dataset[keyword] + options.trackingString +'" class="'+ options.linkClass
                        +'">' + exactWord + '</a>';
                    placeholder = '{_m$d$n_repl$ace_' + placeholderIndex + '_}';
                    placeholderIndex++;
                    text = text.replace(exactWord, placeholder);
                    anchors_new[placeholder] = link;
                    delete dataset[keyword];
                    replaceCount++;
                }
            } else {
                break;
            }
        }

        // Now let's replace placeholders with actual anchor tags, pre-existed ones and new ones.
        for (var l in anchors_existing) {
            text = text.replace(l, anchors_existing[l]);
        }

        for (var l in anchors_new) {
            text = text.replace(l, ' ' + anchors_new[l] + ' ');
        }

        o.innerHTML = text;
    });

    function forEach(arr, callback) {
        if(Array.prototype.forEach) {
            Array.prototype.forEach.call(arr, callback);
        }
        else { // Shim for older browsers that doesn't have array.forEach
            var len = arr.length >>> 0;

            if (typeof callback !== 'function') {
                throw new TypeError();
            }

            var thisArg = arguments.length >= 2 ? arguments[1] : void 0;

            for (var i = 0; i < len; i++)
            {
                if (i in arr) {
                    callback.call(thisArg, arr[i], i, arr);
                }
            }
        }
    }

    function extend (out) {
        out = out || {};

        for (var i = 1; i < arguments.length; i++) {
            if (!arguments[i])
                continue;

            for (var key in arguments[i]) {
                if (arguments[i].hasOwnProperty(key))
                    out[key] = arguments[i][key];
            }
        }

        return out;
    };
};

