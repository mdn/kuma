import React from 'react';
import { render } from '@testing-library/react';
import { AccountSettingsPage } from './routes.jsx';

describe('AccountSettingsPage', () => {
    const mockData = { contributionSupportEmail: 'mock-support@mozilla.com' };

    it('renders Landing page by default', () => {
        const { queryByTestId } = render(
            <AccountSettingsPage slug="/" data={mockData} />
        );
        expect(queryByTestId('landing-page')).toBeInTheDocument();
    });
});
