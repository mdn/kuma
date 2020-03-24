//@flow
import React from 'react';
import ShallowRenderer from 'react-test-renderer/shallow';
import ThankYouPage from '../thank-you.jsx';

describe('Payments Thank You page', () => {
    test('it renders', () => {
        const renderer = new ShallowRenderer();
        renderer.render(<ThankYouPage />);
        const result = renderer.getRenderOutput();
        expect(result).toMatchSnapshot();
    });
});
