//@flow
import React from 'react';
import { render, fireEvent, cleanup } from '@testing-library/react';
import FeedbackForm from '../feedback-form.jsx';

const setup = () => {
    const utils = render(<FeedbackForm />);
    const input = utils.getByPlaceholderText(/enter optional feedback…/i);
    const button = utils.getByText(/send/i);
    const successMessage = 'Thank you for your feedback!';
    return {
        input,
        button,
        successMessage,
        ...utils
    };
};

describe('Payments Feedback Form', () => {
    afterEach(cleanup);

    test('it shows a success message and clears input after submission', () => {
        const { input, button, successMessage, queryByText } = setup();
        fireEvent.change(input, {
            target: { value: 'Here is my feedback. Thank you for listening.' }
        });

        // Verify that message is not present before submitting the form
        expect(queryByText(successMessage)).toBeNull();

        // submit form
        fireEvent.click(button);

        // Ensure that message is visible after submission
        expect(successMessage).toBeTruthy();

        // Ensure that form is cleared
        expect(input.value).toBe('');
    });

    test('it hides success message when user edits input after submission', () => {
        const { input, button, successMessage, queryByText } = setup();

        // edit input
        fireEvent.change(input, {
            target: { value: 'Here is my feedback.' }
        });

        // submit form
        fireEvent.click(button);

        // check that success message is there
        expect(queryByText(successMessage)).toBeTruthy();

        // edit input again
        fireEvent.change(input, {
            target: { value: 'I have more to say' }
        });

        // check that message is not there
        expect(queryByText(successMessage)).toBeNull();
    });

    test('a call to GA is made', () => {
        const { input, button } = setup();
        const feedback = 'Thank you for listening.';
        const mockGA = jest.fn();

        window.ga = mockGA;

        // edit input
        fireEvent.change(input, {
            target: { value: feedback }
        });

        // submit form
        fireEvent.click(button);

        // check that our GA event was called
        expect(mockGA).toHaveBeenCalledWith('send', {
            eventAction: 'feedback',
            eventCategory: 'monthly payments',
            eventLabel: feedback,
            hitType: 'event'
        });
    });
});
