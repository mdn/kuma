(function($) {
    'use strict';

    // Fudge a few languages
    var languages = Prism.languages;
    languages.xml = languages.xul = languages.html = languages.markup;
    languages.js = languages.javascript;
    languages.cpp = languages.clike;

    // Style all as HTML initially
    var defaultBrush = 'html';

    // Treat and highlight PRE elements!
    $('article pre:not(.twopartsyntaxbox):not(.syntaxbox)').each(function() {
        var $pre = $(this);
        var klass = $.trim($pre.attr('class'));

        var brush = defaultBrush;
        var lineSearch;

        // If there are *any* tags within the $pre block, then bail. It might be
        // existing <code> tags (put there for a copy-and-paste) or the pre block
        // has its own tags like <sub>. Don't attempt to syntax highlight these.
        if ($pre.find('*').length) {
            return;
        }

        // Parse classname to look for brush
        var brushSearch = klass.match(/brush: ?(.*)/);
        if (brushSearch && brushSearch[1]) {
            // Split on ';' to accommodate for old line numbering
            brush = $.trim(
                brushSearch[1]
                    .replace(';', ' ')
                    .split(' ')[0]
                    .toLowerCase()
            );
        }

        if (!$pre.hasClass('no-line-numbers')) {
            // Prism upgrade requires adding a class to use line numbering
            $pre.addClass('line-numbers');
        }

        // Format <pre> content for Prism highlighting
        $pre.html(
            '<code class="' +
                // Don't highlight languages unknown to Prism
                (brush in languages ? 'language-' + brush : '') +
                '">' +
                $.trim($pre.html()) +
                '</code>'
        );

        // Do we need to highlight any lines?
        // Legacy format: highlight:[8,9,10,11,17,18,19,20]
        lineSearch = klass.match(/highlight:? ?\[(.*)\]/);
        if (lineSearch && lineSearch[1]) {
            $pre.attr('data-line', lineSearch[1]);
        }
    });

    Prism.highlightAll();
})(jQuery);
