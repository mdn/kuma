// The React version of this code is in the highlightSections() function
// of kuma/javascript/src/article.jsx
(function($) {
    'use strict';

    // find all targets and wrap appropriately
    function highlight(targets) {
        var $targets = $(targets);
        $targets.each(function() {
            $(this)
                .addClass('highlight-spanned')
                .wrapInner('<span class="highlight-span"></span>');
        });
    }

    var $articleSubHeads;
    $articleSubHeads = $('#wikiArticle h3, #wikiArticle h5');
    highlight($articleSubHeads);
})(jQuery);
