import React from 'react';
import { render } from '@testing-library/react';
import { toBeInTheDocument } from '@testing-library/jest-dom/matchers';
import TermsPage, { title } from './terms.jsx';

expect.extend({ toBeInTheDocument });

describe('Payments Terms page', () => {
    it('renders', () => {
        const mockEmail = 'mock-support@mozilla.com';

        const { queryByText } = render(
            <TermsPage data={{ contributionSupportEmail: mockEmail }} />
        );

        // Subheader
        expect(queryByText(title)).toBeInTheDocument();

        // Email
        expect(queryByText(mockEmail)).toBeInTheDocument();

        // Section headers
        expect(queryByText(/^Payment Authorization$/)).toBeInTheDocument();
        expect(queryByText(/^Cancellation$/)).toBeInTheDocument();
        expect(queryByText(/^Privacy Notice$/)).toBeInTheDocument();
    });
});
