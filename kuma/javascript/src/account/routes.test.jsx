import React from 'react';
import { render } from '@testing-library/react';
import { AccountPage } from './routes.jsx';

describe('AccountPage', () => {
    it('renders Landing page by default', () => {
        const { queryByTestId } = render(<AccountPage slug="/" />);
        expect(queryByTestId('landing-page')).toBeInTheDocument();
    });
});
