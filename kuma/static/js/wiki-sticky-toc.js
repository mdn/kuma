(function ($, win, doc) {
    'use strict';

    // list of TOC items
    var tocLinks = ['Syntax', 'Description', 'Constructor', 'Properties', 'Methods', 'Examples', 'Example', 'Live examples', 'Specification', 'Specifications', 'Browser Compatibility', 'Browser compatibility', 'See also']

    // is this a docs page?
    var isDocsPage = location.pathname.toString().indexOf('/en-US/docs/') === 0 ? true : false;
    if(!isDocsPage) {
        return;
    }

    // hide toc
    $('#toc').toggle();

    // attach the sticky TOC to the document
    var $stickyTOC = $('<div id="stickyTOC"></div>');
    var $center = $('<div class="center"></div>');
    var $heading = $('<div class="sticky-head">Jump to section:</div>');
    $heading.appendTo($center);
    $center.appendTo($stickyTOC);

    $(tocLinks).each(function(index) {
        var slug = (tocLinks[index].toString()).replace(' ', '_');
        if($('h2#' + slug).length){
            $('<a href="#' + slug + '">' + tocLinks[index] + '</a>').appendTo($center);
        }
    });
    $stickyTOC.insertAfter('#wiki-document-head');

    if($('#stickyTOC a').length > 0) {
        // add TOC
        $('body').addClass('hasStickyTOC');
    } else {
        $stickyTOC.remove();
    }




}(jQuery, window, document));
