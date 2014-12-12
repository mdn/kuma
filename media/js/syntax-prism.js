(function($) {
    'use strict';

    // Fudge a few languages
    var languages = Prism.languages;
    languages.xml = languages.xul = languages.html = languages.markup;
    languages.js = languages.javascript;
    languages.cpp = languages.clike;

    var defaultBrush = 'html';

    // Treat and highlight PRE elements!
    $('article pre:not(.twopartsyntaxbox):not(.syntaxbox)').each(function() {
        var $pre = $(this);
        var klass = $.trim($pre.attr('class'));

        // Split on ';' to accommodate for old line numbering
        var brush = defaultBrush;
        var lineSearch;

        // Parse classname to look for brush
        var brushSearch = klass.match(/brush: ?(.*)/);
        if(brushSearch && brushSearch[1]) {
            brush = $.trim(brushSearch[1].replace(';', ' ').split(' ')[0].toLowerCase());
        }

        // Some boxes shouldn't be numbered
        if($pre.hasClass('syntaxbox') || $pre.hasClass('twopartsyntaxbox')) {
          $pre.attr('data-prism-prevent-line-number', 1);
        }

        // Style all as HTML initially
        $pre.addClass('language-' + defaultBrush);

        // Format PRE content for Prism highlighting
        $pre.html('<code class="language-' + brush + '">' + $.trim($pre.html()) + '</code>');

        // Do we need to highlight any lines?
        // Legacy format: highlight:[8,9,10,11,17,18,19,20]
        lineSearch = klass.match(/highlight:? ?\[(.*)\]/);
        if(lineSearch && lineSearch[1]) {
            $pre.attr('data-line', lineSearch[1]);
        }
    });

    Prism.highlightAll();

})(jQuery);
