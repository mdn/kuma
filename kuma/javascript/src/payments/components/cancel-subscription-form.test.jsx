import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import { toBeVisible, toBeDisabled } from '@testing-library/jest-dom/matchers';
import CancelSubscriptionForm from './cancel-subscription-form.jsx';
import { SUBSCRIPTIONS_URL } from '../api.js';

// Fixes "ReferenceError: regeneratorRuntime is not defined"
// when running tests that use fetch
require('regenerator-runtime/runtime');

expect.extend({ toBeVisible, toBeDisabled });

const setup = (props = {}) => {
    const mockProps = {
        setShowForm: () => {},
        onSuccess: () => {},
        date: 'April 22, 2020',
        ...props,
    };
    const utils = render(<CancelSubscriptionForm {...mockProps} />);
    const cancelBtn = utils.getByText(/keep my membership/i);
    const submitBtn = utils.getByText(/cancel subscription/i);

    return {
        cancelBtn,
        submitBtn,
        ...utils,
    };
};

describe('Cancel Subscriptions Form', () => {
    it('calls setShowForm() with false if cancel button is clicked', () => {
        const mockProps = {
            setShowForm: jest.fn(),
        };
        const { cancelBtn } = setup(mockProps);
        fireEvent.click(cancelBtn);
        expect(mockProps.setShowForm).toHaveBeenCalledWith(false);
    });

    it('submits and disables form when submit button is clicked', async () => {
        const { submitBtn } = setup();
        const mockOptions = {
            headers: {
                'X-CSRFToken': null,
            },
            method: 'DELETE',
        };

        // Mock fetch and submit form
        window.fetch = jest.fn(() => Promise.resolve({ ok: true }));
        fireEvent.click(submitBtn);

        // Check that button is disabled
        expect(submitBtn).toBeDisabled();

        // Check that fetch was called with correct url and data
        await waitFor(() => {
            expect(window.fetch).toHaveBeenCalledWith(
                SUBSCRIPTIONS_URL,
                mockOptions
            );
            window.fetch.mockReset();
        });
    });

    it('calls onSuccess() when delete is successful', async () => {
        const mockProps = {
            onSuccess: jest.fn(),
        };
        const { submitBtn } = setup(mockProps);

        // Mock fetch and submit form
        window.fetch = jest.fn(() => Promise.resolve({ ok: true }));
        fireEvent.click(submitBtn);

        await waitFor(() => {
            expect(mockProps.onSuccess).toHaveBeenCalled();
            window.fetch.mockReset();
        });
    });

    it('shows error message when delete goes wrong', async () => {
        const { submitBtn, getByText } = setup();

        // Mock bad fetch
        window.fetch = jest.fn(() => Promise.resolve({ ok: false }));

        // Mock window.mdn
        window.mdn = {
            contributionSupportEmail: 'mock-support@mozilla.com',
        };

        // Submit form
        fireEvent.click(submitBtn);

        await waitFor(() => {
            expect(getByText(/sorry, something went wrong/i)).toBeVisible();
            window.fetch.mockReset();
        });
    });
});
