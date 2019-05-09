import React from 'react';
import { renderToString } from 'react-dom/server';

import App from './app.jsx';

/*
 * This function performs server-side rendering of our UI, given
 * a JSON object of document data. It is used by ../ssr-server.js
 */
export default function ssr(data) {
    return renderToString(
        <App documentData={data.documentData} requestData={data.requestData} />
    );
}
