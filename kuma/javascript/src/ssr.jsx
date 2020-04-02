import React from 'react';
import { renderToString } from 'react-dom/server';
import jsesc from 'jsesc';
import App from './app.jsx';
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
        isScriptContext: true,
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

    let html = '';

    try {
        html = renderToString(
            <App componentName={componentName} data={data} />
        );
    } catch (error) {
        if (
            error.message.indexOf(
                `Cannot render or hydrate unknown component: ${componentName}`
            ) === -1
        ) {
            throw error;
        }

        console.error(error.message);
    }

    return { html, script: stringifySafely(data) };
}
