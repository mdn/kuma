(function($) {
    // Fudge a few languages
    var languages = Prism.languages;
    languages.xml = languages.xul = languages.html = languages.markup;
    languages.js = languages.javascript;
    languages.cpp = languages.clike;

    // Treat and highlight PRE elements!
    $('pre').each(function() {
        var $pre = $(this),
            defaultBrush = 'html',
            klass = $.trim($pre.attr('class')),
            // Split on ';' to accommodate for old line numbering
            semiSplit = klass.split(';'),
            klassParts = semiSplit[0].split(':');

        // Style all as HTML initially
        $pre.addClass('language-' + defaultBrush);

        // Some boxes shouldn't be numbered
        if($pre.hasClass('syntaxbox') || $pre.hasClass('twopartsyntaxbox')) {
          $pre.attr('data-prism-prevent-line-number', 1);
        }
        
        // Format PRE content for Prism highlighting
        if(klassParts[0] == 'brush') {
            var brush = $.trim(klassParts[1].toLowerCase());
            brush = languages[brush] ? brush : defaultBrush;
            $pre.html('<code class="language-' + brush + '">' + $.trim($pre.html()) + '</code>');
        }

        // Accommodate for line-highlighting
        // highlight:[8,9,10,11,17,18,19,20]
        if(semiSplit.length > 1) {
            var lines = semiSplit[1].match(/\[(.*)\]/);
            if(lines && lines.length > 1) {
                $pre.attr('data-line', lines[1]);
            }
        }
    });
  
    // Use line highlighting if not IE8
    var script = document.createElement('script');
    if('forEach' in Array.prototype) {
      // Capable browsers get syntax highlighting because
      // querySelectorAll isn't easily patchable
      script.src = window.MEDIA_URL + 'prism/plugins/line-highlight/prism-line-highlight.js';
    }
    else {
      patchIE8ForPrism();
      script.src = window.MEDIA_URL + 'prism/plugins/ie8/prism-ie8.js';
    }
    script.onload = function() {
      // Highlight elements now that they've been treated
      Prism.highlightAll();
    };
    document.body.appendChild(script);

    // Patch for IE8 so that Prism works
    function patchIE8ForPrism() {

        // Add Array map
        Array.prototype.map = function(callback, thisArg) {
            var T, A, k, O = Object(this), len = O.length >>> 0;
            if (thisArg) {
              T = thisArg;
            }
            A = new Array(len);
            k = 0;
            while(k < len) {
              var kValue, mappedValue;
              if (k in O) {
                kValue = O[ k ];
                mappedValue = callback.call(T, kValue, k, O);
                A[ k ] = mappedValue;
              }
              k++;
            }
            return A;
        };

        // Add forEach map
        Array.prototype.forEach = function(action, that) {
            for (var i = 0, n = this.length; i < n; i++) {
                if (i in this) {
                    action.call(that, this[i], i, this);
                }
            }
        };
    }
})(jQuery);