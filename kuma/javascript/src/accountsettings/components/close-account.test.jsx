import * as React from 'react';
import { render, screen } from '@testing-library/react';

import CloseAccount from './close-account.jsx';

const getProps = () => {
    return {
        locale: 'en-US',
        username: 'beetlejuice',
    };
};

describe('CloseAccount', () => {
    it('renders close account component', () => {
        render(<CloseAccount {...getProps()} />);

        expect(
            screen.getByRole('region', { name: /Close Account/i })
        ).toBeInTheDocument();

        expect(
            screen.getByRole('link', { name: /Close account/i })
        ).toBeInTheDocument();
    });
});
