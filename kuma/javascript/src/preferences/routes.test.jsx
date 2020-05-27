import React from 'react';
import { render } from '@testing-library/react';
import { PreferencesPage } from './routes.jsx';

describe('PreferencesPage', () => {
    it('renders Landing page by default', () => {
        const { queryByTestId } = render(<PreferencesPage slug="/" />);
        expect(queryByTestId('landing-page')).toBeInTheDocument();
    });
});
