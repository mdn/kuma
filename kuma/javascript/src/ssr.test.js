import React from 'react';
import { renderToString } from 'react-dom/server';

import App from './app.jsx';
import { fakeDocumentData } from './document.test.js';
import ssr from './ssr.jsx';

let mockData = {
    documentData: fakeDocumentData,
    url: 'mock-url',
};

describe('ssr', () => {
    test('renders a HTML string for a valid componentName', () => {
        const htmlString = renderToString(
            <App componentName="SPA" data={mockData} />
        );

        const result = ssr('SPA', mockData);

        expect(result.html).toEqual(htmlString);
    });

    test('writes to console.error with an unknown componentName', () => {
        const originalError = console.error;
        console.error = jest.fn();

        const result = ssr('UNKNOWN_COMPONENT_NAME', mockData);

        expect(console.error).toHaveBeenCalledWith(
            'Cannot render or hydrate unknown component: UNKNOWN_COMPONENT_NAME'
        );
        expect(result.html).toEqual('');

        console.error = originalError;
    });
});
