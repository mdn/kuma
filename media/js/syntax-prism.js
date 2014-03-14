(function($) {
    'use strict';
    
    // Fudge a few languages
    var languages = Prism.languages;
    languages.xml = languages.xul = languages.html = languages.markup;
    languages.js = languages.javascript;
    languages.cpp = languages.clike;

    var defaultBrush = 'html';

    // Treat and highlight PRE elements!
    $('article pre').each(function() {
        var $pre = $(this);
        var klass = $.trim($pre.attr('class'));
        
        // Split on ';' to accommodate for old line numbering
        var semiSplit = klass.split(';');
        var klassParts = semiSplit[0].split(':');
        var brush;
        var lines;

        // Style all as HTML initially
        $pre.addClass('language-' + defaultBrush);

        // Some boxes shouldn't be numbered
        if($pre.hasClass('syntaxbox') || $pre.hasClass('twopartsyntaxbox')) {
          $pre.attr('data-prism-prevent-line-number', 1);
        }
        
        // Format PRE content for Prism highlighting
        if(klassParts[0] == 'brush') {
            brush = $.trim(klassParts[1].toLowerCase());
            brush = languages[brush] ? brush : defaultBrush;
            $pre.html('<code class="language-' + brush + '">' + $.trim($pre.html()) + '</code>');
        }

        // Accommodate for line-highlighting
        // highlight:[8,9,10,11,17,18,19,20]
        if(semiSplit.length > 1) {
            lines = semiSplit[1].match(/\[(.*)\]/);
            if(lines && lines.length > 1) {
                $pre.attr('data-line', lines[1]);
            }
        }
    });
  
    Prism.highlightAll();

})(jQuery);