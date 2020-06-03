import React from 'react';
import { render, screen } from '@testing-library/react';

import UserDetails from './user-details.jsx';
import UserProvider from '../../user-provider.jsx';

const getProps = (mockData = {}) => {
    const mockUserData = {
        ...UserProvider.defaultUserData,
        ...mockData,
    };

    return {
        locale: 'en-US',
        userData: mockUserData,
        sortedLanguages: {
            'en-US': 'English (US)',
            'en-GB': 'English (UK)',
            fr: 'French',
            de: 'German',
        },
    };
};

describe('UserDetails', () => {
    it('renders user details form', () => {
        const username = 'testuser';
        render(<UserDetails {...getProps({ username })} />);

        const form = screen.getByRole('form');
        const newsletterSubscribe = screen.getByRole('checkbox');

        expect(form).toHaveFormValues({
            'user-username': username,
            'user-fullname': '',
            'user-locale': 'en-US',
        });
        expect(newsletterSubscribe).not.toBeChecked();
    });
});
