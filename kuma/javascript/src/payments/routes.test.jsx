import React from 'react';
import { cleanup, render } from '@testing-library/react';
import { toBeInTheDocument } from '@testing-library/jest-dom/matchers';
import { PaymentPage } from './routes.jsx';

expect.extend({ toBeInTheDocument });

describe('PaymentPage', () => {
    afterEach(() => {
        cleanup();
    });

    it('renders Thank You page if path is /thank-you', () => {
        const { queryByTestId } = render(<PaymentPage slug={'/thank-you/'} />);
        expect(queryByTestId('thank-you-page')).toBeInTheDocument();
    });

    it('renders Terms page if /terms', () => {
        const { queryByTestId } = render(<PaymentPage slug={'/terms'} />);
        expect(queryByTestId('terms-page')).toBeInTheDocument();
    });

    it('renders Landing page by default', () => {
        const { queryByTestId } = render(
            <PaymentPage
                slug={'/someotherpath'}
                data={{ email: 'test@mozilla.com' }}
            />
        );
        expect(queryByTestId('landing-page')).toBeInTheDocument();
    });
});
