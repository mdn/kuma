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

describe('Preferences Titlebar', () => {
    it('renders the preferences landing page titlebar', () => {
        const mockData = {
            username: 'dino',
        };
        const { queryByText } = setup(mockData);

        expect(queryByText('Faulty Towers', { exact: false })).toBeNull();

        expect(queryByText(pageTitle, { exact: false })).toBeTruthy();
        expect(queryByText(mockData.username, { exact: false })).toBeTruthy();
    });
});
