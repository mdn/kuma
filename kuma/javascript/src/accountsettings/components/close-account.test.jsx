import * as React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import CloseAccount from './close-account.jsx';

describe('CloseAccount', () => {
    it('renders close account component', () => {
        render(<CloseAccount />);

        expect(
            screen.getByRole('region', { name: /Close Account/i })
        ).toBeInTheDocument();

        expect(
            screen.getByRole('button', { name: /Close account/i })
        ).toBeInTheDocument();
    });

    it('shows close account form when Close account button is clicked', () => {
        render(<CloseAccount />);

        expect(
            screen.queryByRole('form', { name: /Close Account/i })
        ).not.toBeInTheDocument();

        const button = screen.getByRole('button', { name: /Close account/i });
        userEvent.click(button);

        const form = screen.getByRole('form', { name: /Close Account/i });

        expect(form).toBeInTheDocument();
        expect(form).toBeVisible();
    });

    it('hides close account form when keep account button is clicked', () => {
        render(<CloseAccount />);

        const button = screen.getByRole('button', { name: /close account/i });
        userEvent.click(button);

        const keepAccountButton = screen.getByRole('button', {
            name: /keep account/i,
        });
        const form = screen.getByRole('form', { name: /close account/i });

        expect(form).toBeInTheDocument();
        expect(form).toBeVisible();

        userEvent.click(keepAccountButton);

        expect(
            screen.queryByRole('form', { name: /close account/i })
        ).not.toBeInTheDocument();
    });
});
