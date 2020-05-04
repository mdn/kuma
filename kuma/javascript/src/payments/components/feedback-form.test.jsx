//@flow
import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { toHaveAttribute } from '@testing-library/jest-dom/matchers';
import FeedbackForm from './feedback-form.jsx';
import { SUBSCRIPTIONS_FEEDBACK_URL } from '../api.js';

expect.extend({ toHaveAttribute });

const setup = () => {
    const utils = render(<FeedbackForm />);
    const input = utils.getByTestId('feedback-input');
    const button = utils.getByTestId('feedback-button');
    const formId = 'feedback-form';
    const successId = 'success-msg';
    const errorId = 'error-msg';
    const feedback = 'Here is my feedback. Thank you for listening.';
    return {
        input,
        button,
        formId,
        successId,
        errorId,
        feedback,
        ...utils,
    };
};

describe('Payments Feedback Form', () => {
    afterEach(() => {
        window.fetch.mockReset();
    });

    test('it only submits if input value is greater than minimum string length', () => {
        const { input, button, errorId, queryByTestId } = setup();

        window.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        fireEvent.change(input, {
            target: {
                value: 'abc        ',
            },
        });

        // Submit form
        fireEvent.click(button);

        // Check that error message shows and fetch was not called
        expect(queryByTestId(errorId)).toBeTruthy();
        expect(window.fetch).not.toHaveBeenCalled();
    });

    test('it shows a success message, clears and disables input after submission', async () => {
        const {
            input,
            button,
            feedback,
            formId,
            successId,
            queryByTestId,
        } = setup();

        window.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        fireEvent.change(input, {
            target: {
                value: feedback,
            },
        });

        // Verify that message is not present before submitting the form
        expect(queryByTestId(successId)).toBeNull();

        // Submit form
        fireEvent.click(button);

        await waitFor(() => {
            // Check for success message
            expect(queryByTestId(successId)).toBeTruthy();

            // Ensure that the form is gone
            expect(queryByTestId(formId)).toBeNull();
        });
    });

    test('it shows error message when request fails', async () => {
        const {
            input,
            button,
            feedback,
            errorId,
            getByText,
            queryByTestId,
        } = setup();

        // Modify fetch to return ok false
        window.fetch = jest.fn(() => Promise.resolve({ ok: false }));

        window.mdn = {
            contributionSupportEmail: 'mock-support@mozilla.com',
        };

        fireEvent.change(input, {
            target: {
                value: feedback,
            },
        });

        // Verify that error is not present before submitting the form
        expect(queryByTestId(errorId)).toBeNull();

        // Submit form
        fireEvent.click(button);

        await waitFor(() => {
            // Check for error message
            expect(queryByTestId(errorId)).toBeTruthy();

            // Check that our email address was rendered correctly
            expect(
                getByText(window.mdn.contributionSupportEmail)
            ).toHaveAttribute(
                'href',
                `mailto:${window.mdn.contributionSupportEmail}`
            );
        });
    });

    test('fetch() method submits feedback', async () => {
        const { input, button, feedback } = setup();
        const mockOptions = {
            body: JSON.stringify({ feedback }),
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': null,
            },
            method: 'POST',
        };

        window.fetch = jest.fn(() => Promise.resolve({ ok: true }));

        fireEvent.change(input, {
            target: {
                value: feedback,
            },
        });

        // Submit form
        fireEvent.click(button);

        // Check that fetch was called with correct url and data
        await waitFor(() => {
            expect(window.fetch).toHaveBeenCalledWith(
                SUBSCRIPTIONS_FEEDBACK_URL,
                mockOptions
            );
        });
    });
});
