google.load("search", "1", {
    "nocss" : true,
    "nooldnames" : true,
    "language": $("html").attr("lang")
});

$(document).ready(function() {
    // Place branding
    google.search.Search.getBranding(document.getElementById("site-search-gg"));

    /* Run a Google Search through the API */
    var sr = $('#search-results'),
        query = sr.attr("data-q");
    if (!rs.length || !query)
        return;

    // branding
    google.search.Search.getBranding(document.getElementById("google-branding"));

    // restrict to MDN only
    var siteSearch = new google.search.WebSearch();
    siteSearch.setUserDefinedLabel("");
    siteSearch.setSiteRestriction("developer.mozilla.org");
    siteSearch.setLinkTarget(google.search.Search.LINK_TARGET_SELF);
    siteSearch.clearResults();

    var done = function() {
        for (i in siteSearch.results) {
            sr.append(siteSearch.results[i].html.cloneNode(true));
        }

        var cursor = siteSearch.cursor;
        if (!cursor && siteSearch.results.length == 0) {
            sr.html("<p>No results found.</p>");
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