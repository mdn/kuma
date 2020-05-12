import React from 'react';
import { render } from '@testing-library/react';
import { PaymentPage, PAYMENT_PATHS } from './routes.jsx';

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

    it('renders Management page if path contains management', () => {
        const { queryByTestId } = render(
            <PaymentPage slug={PAYMENT_PATHS.MANAGEMENT} />
        );
        expect(queryByTestId('management-page')).toBeInTheDocument();
    });

    it('renders Landing page by default', () => {
        const { queryByTestId } = render(
            <PaymentPage slug={'/'} data={mockData} />
        );
        expect(queryByTestId('landing-page')).toBeInTheDocument();
    });
});
