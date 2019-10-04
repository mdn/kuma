import React from 'react';
import { renderToString } from 'react-dom/server';
import jsesc from 'jsesc';
import SinglePageApp from './single-page-app.jsx';
import LandingPage from './landing-page.jsx';
import SignupFlow from './signup-flow.jsx';
import { localize } from './l10n.js';

/**
 * Inspired by
 * https://joreteg.com/blog/improving-redux-state-transfer-performance
 * This function produces a string that you can inject into an HTML document
 * by putting it like this: `<script>var data = JSON.parse(THIS_STRING)</script>
 */
function stringifySafely(obj) {
    return jsesc(JSON.stringify(obj), {
        json: true,
        isScriptContext: true
    });
}
/*
 * This function performs server-side rendering of our UI, given
 * a JSON object of document data. It is used by ../ssr-server.js
 */
export default function ssr(componentName, data) {
    // Before we can render the specified component, we need to call
    // localize() so that gettext() and ngettext() will work properly
    // during rendering.
    let pluralFunction = null;
    if (data.pluralExpression) {
        // Creating a function like this in client-side JS will usually
        // violate CSP. But we're running in Node here, so it is okay.
        pluralFunction = new Function(
            'n',
            `let v=(${data.pluralExpression});return(v===true)?1:((v===false)?0:v);`
        );
    }

    localize(data.locale, data.stringCatalog, pluralFunction);

    // This switch statement is duplicated in index.jsx. Anything changed
    // here should also be changed there. TODO: refactor this!
    let html = '';
    switch (componentName) {
        case 'SPA':
            // Ideally, we want as much as possible of MDN to be part
            // of the single page app so that we can get client-side
            // navigation between pages. Currently the single page app
            // handles document pages and search results
            html = renderToString(
                <SinglePageApp
                    initialURL={data.url}
                    initialData={data.documentData}
                />
            );
            ['quickLinksHTML', 'bodyHTML', 'tocHTML'].forEach(key => {
                delete data.documentData[key];
            });
            break;
        case 'landing':
            // This is the React UI for the MDN homepage.
            // The homepage has a React-based header, but most of the
            // content is still based on Jinja templates, so we can't
            // currently make it part of the single page app and have
            // to handle it as a special case here.
            html = renderToString(<LandingPage />);
            break;
        case 'signupflow':
            // This is the React UI for the MDN sign-up flow.
            // The signup flow has a React-based header, but most of the
            // content is still based on Jinja templates, so we can't
            // currently make it part of the single page app and have
            // to handle it as a special case here.
            html = renderToString(<SignupFlow />);
            break;
        default:
            console.error(
                'Can not render unknown component name:',
                componentName
            );
            break;
    }

    return { html, script: stringifySafely(data) };
}
