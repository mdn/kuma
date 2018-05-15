'use strict';

const fse = require('fs-extra');
const htmlReporter = require('pa11y-reporter-html');
const pa11y = require('pa11y');

const options = {
    standard: 'WCAG2AA',
    wait: 500
};
const pages = getPages();
const RESULTS_FOLDER = 'pa11y-results';

/**
 * Reads and returns list of URLs from .pa11y config
 * @returns {Object} containing an array of urls
 * Example
 * -------
 * {
 *     "urls": [
 *         "http://localhost:8000/",
 *         "http://localhost:8000/en-US/docs/Web/HTML",
 *         "http://localhost:8000/en-US/docs/Learn",
 *     ]
 * }
 */
function getPages() {
    try {
        return fse.readJsonSync('.pa11y');
    } catch (error) {
        console.error(`Error while loading pages file: ${error}`);
    }
}

/**
 * Runs pa11y against each url in the list of pages and combines the results
 * @param {Object} pages - Object containing a list of urls
 * @returns {Object} containing results gathered on all pages. See
 * https://github.com/pa11y/pa11y#javascript-interface for details on the format
 */
async function testPages(pages) {
    const results = await Promise.all(pages.urls.map((page) => pa11y(page, options)));
    return results;
}

/**
 * Writes results for each individual pages as HTML inside the folder /pa11y-results
 * @param {Object} results - Object containing combined reuslts from `testPages`
 */
async function writeResults(results) {
    try {

        if (fse.pathExistsSync(RESULTS_FOLDER)) {
            // clean it out before writing files
            fse.emptyDirSync(RESULTS_FOLDER);
        }

        for(let result of results) {
            let html = await htmlReporter.results(result);
            let page = result.pageUrl.substr(result.pageUrl.lastIndexOf('/'));
            let pageName = page === '/' ? 'landing' : page;
            fse.outputFileSync(`${RESULTS_FOLDER}/${pageName}.html`, html);
        }
    } catch (error) {
        console.error(`Error while processing and writing results: ${error}`);
    }

}

testPages(pages).then((results) => {
    writeResults(results);
});
