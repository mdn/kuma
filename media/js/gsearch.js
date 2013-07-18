google.load("search", "1", {
    "nocss" : true,
    "nooldnames" : true,
    "language": $("html").attr("lang")
});

$(document).ready(function() {
    // Place branding
    google.search.Search.getBranding($("#site-search-gg")[0]);

    /* Run a Google Search through the API */
    var $sr = $('#search-results'),
        query = $sr.attr("data-q");
    if (!$sr.length || !query)
        return;

    // branding
    google.search.Search.getBranding($("#google-branding")[0]);

    // restrict to MDN only
    var siteSearch = new google.search.WebSearch();
    siteSearch.setUserDefinedLabel("");
    siteSearch.setSiteRestriction("developer.mozilla.org");
    siteSearch.setLinkTarget(google.search.Search.LINK_TARGET_SELF);
    siteSearch.clearResults();

    var done = function() {
        var clone;

        for (i in siteSearch.results) {
            clone = siteSearch.results[i].html.cloneNode(true);

            /* START:  Remove before launch */
            $(clone.childNodes).each(function() {
                var $this = $(this);
                $this.html($this.html().replace(/developer.mozilla\.org/g, window.location.hostname));
            });
            /* FINISH:  Remove before launch */
            
            $sr.append(clone);
        }

        var cursor = siteSearch.cursor;
        if (!cursor && siteSearch.results.length == 0) {
            $sr.html("<p>No results found.</p>");
        } else if (cursor.currentPageIndex < cursor.pages.length - 1) {
            // this is recursive. google.search will re-call its callback, i.e.
            // this function when it gets the next page of result.
            siteSearch.gotoPage(cursor.currentPageIndex + 1);
        }
    }

    // run search
    siteSearch.setSearchCompleteCallback(null, done);
    siteSearch.execute(query);
});