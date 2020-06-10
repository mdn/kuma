import React from 'react';
import { render } from '@testing-library/react';

import { pageTitle } from '../pages/index.jsx';
import Titlebar from './titlebar.jsx';
import UserProvider from '../../user-provider.jsx';

const setup = (mockData = {}) => {
    const mockUserData = {
        ...UserProvider.defaultUserData,
        ...mockData,
    };

    const mockProps = {
        locale: 'en-US',
        pageTitle: pageTitle,
        userData: mockUserData,
    };

    const utils = render(<Titlebar {...mockProps} />);

    return utils;
};

describe('Account Settings Titlebar', () => {
    it('renders the account settings landing page titlebar', () => {
        const { queryByText } = setup();

        expect(queryByText('Faulty Towers', { exact: false })).toBeNull();
        expect(queryByText(pageTitle, { exact: false })).toBeTruthy();
    });
});
