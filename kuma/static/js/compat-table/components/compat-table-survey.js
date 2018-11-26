(function() {
    'use strict';

    var bcdContainer;
    var bcdGithubLink = document.querySelector('.bc-github-link');

    // if there is no Github link, do nothing
    if (!bcdGithubLink) {
        return;
    }

    /**
     * Creates and returns the survey link HTML
     * @returns survey link HTML
     */
    function surveyLink() {
        var container = document.createElement('div');
        var surveyLink = document.createElement('a');
        var linkHref = 'https://www.surveygizmo.com/s3/4637778/browser-compat';

        surveyLink.setAttribute('href', linkHref);
        surveyLink.setAttribute('rel', 'external noopener');
        surveyLink.setAttribute('target', '_blank');
        surveyLink.textContent = 'Take this quick survey to help us improve our browser compatibility tables';

        container.setAttribute('class', 'survey-link-container');
        container.appendChild(surveyLink);

        return container;
    }

    bcdContainer = document.querySelector('.bc-data');
    bcdContainer.insertAdjacentElement('beforebegin', surveyLink());
})();
