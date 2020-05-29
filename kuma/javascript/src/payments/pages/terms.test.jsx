import React from 'react';
import { render } from '@testing-library/react';
import TermsPage, { title } from './terms.jsx';

describe('Payments Terms page', () => {
    it('renders', () => {
        const { queryByText, getByTestId } = render(<TermsPage />);

        // Subheader
        expect(getByTestId('subheader')).toHaveTextContent(title);

        // Section headers
        expect(queryByText(/^Payment Authorization$/)).toBeInTheDocument();
        expect(queryByText(/^Cancellation$/)).toBeInTheDocument();
        expect(queryByText(/^Privacy Notice$/)).toBeInTheDocument();
    });
});
