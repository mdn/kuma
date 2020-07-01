import * as React from 'react';
import { render, screen } from '@testing-library/react';
import UserEvent from '@testing-library/user-event';

import CloseAccountForm, { title } from './close-account-form.jsx';

describe('CloseAccountForm', () => {
    it('renders form', () => {
        const onCancel = jest.fn();

        render(<CloseAccountForm onCancel={onCancel} />);

        const closeAccountButton = screen.getByRole('button', {
            name: /Yes, close account/i,
        });
        const keepAccountButton = screen.getByRole('button', {
            name: /keep account/i,
        });

        expect(screen.getByText(title)).toBeInTheDocument();
        expect(closeAccountButton).toBeInTheDocument();
        expect(keepAccountButton).toBeInTheDocument();
    });

    it('calls onCancel when keep account button is clicked', () => {
        const onCancel = jest.fn();

        render(<CloseAccountForm onCancel={onCancel} />);

        const keepAccountButton = screen.getByRole('button', {
            name: /keep account/i,
        });

        UserEvent.click(keepAccountButton);
        expect(onCancel).toHaveBeenCalled();
    });

    it('disables the close account button when button is clicked', () => {
        const onCancel = jest.fn();

        render(<CloseAccountForm onCancel={onCancel} />);

        const closeAccountButton = screen.getByRole('button', {
            name: /Yes, close account/i,
        });

        UserEvent.click(closeAccountButton);
        expect(closeAccountButton).toBeDisabled();
    });
});
