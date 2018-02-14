(function() {
    'use strict';

    var collapseSearchButton = document.getElementById('close-header-search');
    var header = document.getElementById('main-header');
    var isExpanded = false;
    var navMainSearchForm = document.getElementById('nav-main-search');
    var searchInput = document.getElementById('main-q');
    var searchWrap = navMainSearchForm.querySelector('.search-wrap');
    var toolboxContainer = document.getElementById('toolbox');

    /**
     * Used as the callback to the `transitionend` event in `collapseSearch`
     */
    function collapsed() {
        toolboxContainer.classList.remove('hidden');
        searchInput.setAttribute('aria-hidden', true);
        isExpanded = false;
        // remove the event listener so it is not called during expandSearch
        searchWrap.removeEventListener('transitionend', collapsed, false);
    }

    /**
     * Expands the search field, updates the aria-hidden attribute,
     * and set isExanded to true.
     */
    function expandSearch() {
        toolboxContainer.classList.add('hidden');
        header.classList.add('expanded');

        searchInput.setAttribute('aria-hidden', false);

        searchInput.focus();
        isExpanded = true;
    }

    /**
     * Collapses the search field, updates the aria-hidden attribute,
     * and set isExanded to false.
     */
    function collapseSearch() {
        header.classList.remove('expanded');
        searchWrap.addEventListener('transitionend', collapsed, false);
    }

    navMainSearchForm.addEventListener('click', function() {
        if(!isExpanded) {
            expandSearch();
        }
    });

    searchInput.addEventListener('blur', collapseSearch);

    searchInput.addEventListener('focus', function() {
        if(!isExpanded) {
            expandSearch();
        }
    });

    searchInput.addEventListener('keyup', function(event) {
        // user pressed Escape and the form is expanded
        if (event.key === 'Escape' && isExpanded) {
            searchInput.blur();
        }
    });

    collapseSearchButton.addEventListener('click', collapseSearch);

})();
