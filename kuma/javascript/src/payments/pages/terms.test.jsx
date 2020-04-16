import React from 'react';
import { render } from '@testing-library/react';
import {
    toBeInTheDocument,
    toHaveTextContent,
} from '@testing-library/jest-dom/matchers';
import TermsPage, { title } from './terms.jsx';

expect.extend({ toBeInTheDocument, toHaveTextContent });

describe('Payments Terms page', () => {
    it('renders', () => {
        const mockEmail = 'mock-support@mozilla.com';

        const { queryByText, getByTestId } = render(
            <TermsPage data={{ contributionSupportEmail: mockEmail }} />
        );

        // Subheader
        expect(getByTestId('subheader')).toHaveTextContent(title);

        // Email
        expect(queryByText(mockEmail)).toBeInTheDocument();

        // Section headers
        expect(queryByText(/^Payment Authorization$/)).toBeInTheDocument();
        expect(queryByText(/^Cancellation$/)).toBeInTheDocument();
        expect(queryByText(/^Privacy Notice$/)).toBeInTheDocument();
    });
});
