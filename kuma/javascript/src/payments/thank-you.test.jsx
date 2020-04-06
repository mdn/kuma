//@flow
import React from 'react';
import { render } from '@testing-library/react';
import ThankYouPage from './thank-you.jsx';
import { title } from './thank-you-subheader.jsx';

describe('Payments Thank You page', () => {
    test('it renders', () => {
        // Ensure that subheader, useful things, and feedback form renders
        const { queryByText, queryByTestId } = render(<ThankYouPage />);

        // Subheader
        expect(queryByText(title)).toBeTruthy();

        // Useful things section
        expect(queryByTestId('useful-things')).toBeTruthy();

        // Feedback form
        expect(queryByTestId('feedback-form')).toBeTruthy();
    });
});
