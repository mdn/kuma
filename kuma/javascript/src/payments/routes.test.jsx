import React from 'react';
import { render } from '@testing-library/react';
import { toBeInTheDocument } from '@testing-library/jest-dom/matchers';
import { PaymentPage, PAYMENT_PATHS } from './routes.jsx';

expect.extend({ toBeInTheDocument });

describe('PaymentPage', () => {
    const mockData = { email: 'mock-support@mozilla.com' };
    it('renders Thank You page if path contains thank-you', () => {
        const { queryByTestId } = render(
            <PaymentPage slug={PAYMENT_PATHS.THANK_YOU} />
        );
        expect(queryByTestId('thank-you-page')).toBeInTheDocument();
    });

    it('renders Terms page if path contains terms', () => {
        const { queryByTestId } = render(
            <PaymentPage slug={PAYMENT_PATHS.TERMS} data={mockData} />
        );
        expect(queryByTestId('terms-page')).toBeInTheDocument();
    });

    it('renders Landing page by default', () => {
        const { queryByTestId } = render(
            <PaymentPage slug={'/'} data={mockData} />
        );
        expect(queryByTestId('landing-page')).toBeInTheDocument();
    });
});
