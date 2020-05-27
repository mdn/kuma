import React from 'react';
import { render } from '@testing-library/react';
import { AccountSettingsPage } from './routes.jsx';

describe('AccountSettingsPage', () => {
    it('renders Landing page by default', () => {
        const { queryByTestId } = render(<AccountSettingsPage slug="/" />);
        expect(queryByTestId('landing-page')).toBeInTheDocument();
    });
});
