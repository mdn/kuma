(function($, win) {
    'use strict';

    // find all targets and wrap appropriately
    function highlight(targets) {
        var $targets = $(targets);
        $targets.each(function() {
            $(this).addClass('highlight-spanned').wrapInner('<span class="highlight-span"></span>');
        });
    }

    var $articleSubHeads;
    // call on aritcle body with targets
    if(!win.waffle || !win.waffle.flag_is_active('line_length')) {
        $articleSubHeads = $('#wikiArticle h2');
    } else {
        $articleSubHeads = $('#wikiArticle h3, #wikiArticle h5');
    }
    highlight($articleSubHeads);

})(jQuery, window);
