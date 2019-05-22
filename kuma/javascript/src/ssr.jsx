import React from 'react';
import { renderToString } from 'react-dom/server';

import App from './app.jsx';
import { localize } from './l10n.js';

/*
 * This function performs server-side rendering of our UI, given
 * a JSON object of document data. It is used by ../ssr-server.js
 */
export default function ssr(data) {
    // Before we can render the App, we need to call localize() so that
    // gettext() and ngettext() will work property during rendering.
    let pluralFunction = null;
    if (data.pluralExpression) {
        // Creating a function like this in client-side JS will usually
        // violate CSP. But we're running in Node here, so it is okay.
        pluralFunction = new Function(
            'n',
            `let v=(${
                data.pluralExpression
            });return(v===true)?1:((v===false)?0:v);`
        );
    }
    localize(data.requestData.locale, data.stringCatalog, pluralFunction);

    return renderToString(<App documentData={data.documentData} />);
}
