(function($) {
    'use strict';

    // find all targets and wrap appropriately
    function highlight(targets) {
        var $targets = $(targets);
        $targets.each(function() {
            $(this).addClass('highlight-spanned').wrapInner('<span class="highlight-span"></span>');
        });
    }

    // call on aritcle body with targets
    var $articleSubHeads = $('#wikiArticle h3, #wikiArticle h5');
    highlight($articleSubHeads);

})(jQuery);
