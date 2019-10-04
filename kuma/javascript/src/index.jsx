// @flow
import React from 'react';
import ReactDOM from 'react-dom';

import SinglePageApp from './single-page-app.jsx';
import LandingPage from './landing-page.jsx';
import SignupFlow from './signup-flow.jsx';
import { AppErrorBoundary } from './error-boundaries.jsx';
import { localize } from './l10n.js';

let container = document.getElementById('react-container');
if (container) {
    let componentName = container.dataset.componentName;

    // The HTML page that loads this code is expected to have an inline
    // script that sets this window._document_data property to an object
    // with all the data needed to hydrate or render the UI.
    let data = window._react_data;

    let quickLinksHTMLElement = document.querySelector('.sidebar .quick-links');
    if (quickLinksHTMLElement) {
        data.documentData.quickLinksHTML = quickLinksHTMLElement.innerHTML;
    }
    let wikiArticleElement = document.querySelector('#wikiArticle');
    if (wikiArticleElement) {
        data.documentData.bodyHTML = wikiArticleElement.innerHTML;
    }

    let tocElement = document.querySelector('.document-toc ul');
    if (tocElement) {
        data.documentData.tocHTML = tocElement.innerHTML;
    }

    // Store the string catalog so that l10n.gettext() can do translations
    localize(data.locale, data.stringCatalog, data.pluralFunction);

    let app = null;
    // This switch statement is duplicated in ssr.jsx. Anything changed
    // here should also be changed there. TODO: refactor this!
    switch (componentName) {
        case 'SPA':
            // Ideally, we want as much as possible of MDN to be part
            // of the single page app so that we can get client-side
            // navigation between pages. Currently the single page app
            // handles document pages and search results
            app = (
                <SinglePageApp
                    initialURL={data.url}
                    initialData={data.documentData}
                />
            );
            break;
        case 'landing':
            // This is the React UI for the MDN homepage.
            // The homepage has a React-based header, but most of the
            // content is still based on Jinja templates, so we can't
            // currently make it part of the single page app and have
            // to handle it as a special case here.
            app = <LandingPage />;
            break;
        case 'signupflow':
            // This is the React UI for the MDN sign-up flow.
            // The signup flow has a React-based header, but most of the
            // content is still based on Jinja templates, so we can't
            // currently make it part of the single page app and have
            // to handle it as a special case here.
            app = <SignupFlow />;
            break;
        case 'default':
            throw new Error(
                `Cannot render or hydrate unknown component: ${componentName}`
            );
    }

    /* StrictMode is a tool for highlighting potential problems
       in an application. Like Fragment, StrictMode does not
       render any visible UI. It activates additional checks and
       warnings for its descendants.
       @see https://reactjs.org/docs/strict-mode.html */
    app = <React.StrictMode>{app}</React.StrictMode>;

    /* Need docstring*/
    app = <AppErrorBoundary>{app}</AppErrorBoundary>;

    // NOTE: `document.all` is only available in lte IE10
    // $FlowFixMe
    const isIE10 = document.all;
    // IE11 specific https://stackoverflow.com/questions/17907445/how-to-detect-ie11#answer-22082397
    const isIE11 = !!window.MSInputMethodContext && !!document.documentMode;
    if (container.firstElementChild) {
        /* If the container element is not empty, then it was presumably
         * rendered on the server, and we just need to hydrate it now.
         *
         * If we're running under google translate, however, we skip
         * the hydration step because the mismatched origins cause
         * errors and cause all the content to disappear when React
         * unmounts the components. We also do not hydrate if in IE10+.
         * It is better for the end user in this case to just get a
         * static HTML page.
         * See Bug 1562293, and https://github.com/mozilla/kuma/issues/5786
         */
        if (
            window.origin !== 'https://translate.googleusercontent.com' &&
            !isIE10 &&
            !isIE11
        ) {
            ReactDOM.hydrate(app, container);
        }
    } else {
        // Otherwise, if the container is empty, then we need to do a full
        // client-side render. The goal is that pages should always be
        // server-side rendered when first loaded (for speed and SEO). But
        // this is here for robustness in case there are errors during
        // server side rendering.
        //
        // Also, local front-end work is easier if you stop the SSR
        // server (with `docker-compose stop ssr`) and allow your UX
        // to be rendered on the client side. Otherwise you will have
        // to restart the SSR server (with `docker-compose restart ssr`)
        // every time you want to try out a code change.
        ReactDOM.render(app, container);
    }

    // Finally, here is some other miscellaneous code that we need to run.
    // The idea is that this is code needed to make the non-React parts of
    // the UX work correctly. If we end up with more than a couple of things
    // here, we should refactor them into a separate module

    // An event handler to make the language selector menu
    // in the footer work correctly.
    // See also kuma/static/js/main.js where similar code appears to
    // make the menu work on the wiki domain
    for (let menu of document.querySelectorAll('select.autosubmit')) {
        menu.addEventListener('change', function() {
            this.form.submit();
        });
    }
}
