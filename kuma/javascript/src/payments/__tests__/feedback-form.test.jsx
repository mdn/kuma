//@flow
import React from 'react';
import { render, fireEvent, cleanup, waitFor } from '@testing-library/react';
import FeedbackForm, { FEEDBACK_URL } from '../feedback-form.jsx';

const setup = () => {
    const utils = render(<FeedbackForm />);
    const input = utils.getByTestId('feedback-input');
    const button = utils.getByTestId('feedback-button');
    const successId = 'success-msg';
    const errorId = 'error-msg';
    const feedback = 'Here is my feedback. Thank you for listening.';
    return {
        input,
        button,
        successId,
        errorId,
        feedback,
        ...utils
    };
};

describe('Payments Feedback Form', () => {
    afterEach(() => {
        cleanup();
        window.fetch.mockReset();
    });

    test('it shows a success message, clears and disables input after submission', async () => {
        const { input, button, feedback, successId, queryByTestId } = setup();

        window.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        fireEvent.change(input, {
            target: {
                value: feedback
            }
        });

        // Verify that message is not present before submitting the form
        expect(queryByTestId(successId)).toBeNull();

        // Submit form
        fireEvent.click(button);

        await waitFor(() => {
            // Ensure that form is cleared
            expect(input.value).toBe('');

            // Ensure that the input is disabled
            expect(input.disabled).toBeTruthy();

            // Check for success message
            expect(queryByTestId(successId)).toBeTruthy();
        });
    });

    test('it shows error message when request fails', async () => {
        const { input, button, feedback, errorId, queryByTestId } = setup();

        // Modify fetch to return ok false
        window.fetch = jest.fn(() => Promise.resolve({ ok: false }));

        fireEvent.change(input, {
            target: {
                value: feedback
            }
        });

        // Verify that error is not present before submitting the form
        expect(queryByTestId(errorId)).toBeNull();

        // Submit form
        fireEvent.click(button);

        await waitFor(() => {
            // Check for error message
            expect(queryByTestId(errorId)).toBeTruthy();
        });
    });

    test('fetch() method submits feedback', async () => {
        const { input, button, feedback } = setup();
        const mockArgs = {
            url: FEEDBACK_URL,
            options: {
                body: JSON.stringify({ feedback }),
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': null
                },
                method: 'POST'
            }
        };

        window.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        fireEvent.change(input, {
            target: {
                value: feedback
            }
        });

        // Submit form
        fireEvent.click(button);

        // Check that fetch was called with correct url and data
        await waitFor(() => {
            expect(window.fetch).toHaveBeenCalledWith(
                mockArgs.url,
                mockArgs.options
            );
        });
    });
});
