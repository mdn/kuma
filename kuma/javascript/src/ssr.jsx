import React from 'react';
import { renderToString } from 'react-dom/server';

import SinglePageApp from './single-page-app.jsx';
import LandingPage from './landing-page.jsx';
import { localize } from './l10n.js';

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
            `let v=(${
                data.pluralExpression
            });return(v===true)?1:((v===false)?0:v);`
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
            break;
        case 'landing':
            // This is the React UI for the MDN homepage.
            // The homepage has a React-based header, but most of the
            // content is still based on Jinja templates, so we can't
            // currently make it part of the single page app and have
            // to handle it as a special case here.
            html = renderToString(<LandingPage />);
            break;
        default:
            console.error(
                'Can not render unknown component name:',
                componentName
            );
            break;
    }

    // TODO: the server-side rendered HTML will include a lot of
    // separate little stylesheets becasue that is the way Emotion
    // outputs them when server-side rendering. Arguably, this might be
    // the fastest way to render content above-the-fold because styles
    // further down in the document don't need to be parsed until they
    // are actually needed. But it does seem like it would be inefficient
    // to have dozens of separate stylesheets to parse. We need data
    // on this, I suppose.
    //
    // I attempted to consolidate the stylesheets with the following
    // code, but it turned out to break the hydration process because
    // emotion expect to have all of the separate stylesheets. So if you
    // uncomment this code, you'll get a single big stylesheet, but the
    // page will re-render after loading, which is worse than the problem
    // we were trying to solve:
    //
    // Post-process the HTML string we to consolidate
    // all of the emotion stylesheets into a single one.
    // let stylesheets = [];
    // html = html.replace(
    //     /<style data-emotion-css="[^"]+">(.*?)<\/style>/g,
    //     function(match, styles) {
    //         stylesheets.push(styles);
    //         return '';
    //     }
    // );
    // return `<style>\n${stylesheets.join('\n')}\n</style>\n${html}`;
    //
    return html;
}
