import React from 'react';
import { renderToString } from 'react-dom/server';

import App from './app.jsx';
import { localize } from './l10n.js';

/*
 * This function performs server-side rendering of our UI, given
 * a JSON object of document data. It is used by ../ssr-server.js
 */
export default function ssr(data) {
    // Store the string catalog so that l10n.gettext() can do translations
    localize(data.requestData.locale, data.localizationData);

    return renderToString(<App documentData={data.documentData} />);
}
