import React from 'react';
import { render } from '@testing-library/react';
import { toBeInTheDocument } from '@testing-library/jest-dom/matchers';
import TermsPage, { title } from './terms.jsx';

expect.extend({ toBeInTheDocument });

describe('Payments Terms page', () => {
    it('renders', () => {
        const { queryByText } = render(<TermsPage />);

        // Subheader
        expect(queryByText(title)).toBeInTheDocument();

        // Section headers
        expect(queryByText(/^Payment Terms$/)).toBeInTheDocument();
        expect(queryByText(/^Payment Authorization$/)).toBeInTheDocument();
        expect(queryByText(/^Cancellation$/)).toBeInTheDocument();
        expect(queryByText(/^Privacy Notice$/)).toBeInTheDocument();
    });
});
