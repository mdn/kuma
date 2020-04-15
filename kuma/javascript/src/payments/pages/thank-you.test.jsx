//@flow
import React from 'react';
import { render } from '@testing-library/react';
import UserProvider from '../../user-provider.jsx';
import { interpolate } from '../../l10n.js';
import ThankYouPage from './thank-you.jsx';
import { title, subtitle } from '../components/subheaders/thank-you.jsx';
import {
    nonSubscriberInvitationCopy,
    subscriberInvitationCopy,
} from '../components/incentives.jsx';

describe('Payments Thank You page', () => {
    test('it renders', () => {
        // Ensure that subheader, useful things, and feedback form renders
        const { queryByText, queryByTestId } = render(
            <ThankYouPage locale="fr" />
        );

        // Subheader
        expect(queryByText(title)).toBeTruthy();

        // Useful things section
        expect(queryByTestId('useful-things')).toBeTruthy();

        // Feedback form
        expect(queryByTestId('feedback-form')).toBeTruthy();

        // Render non-subscriber invitations copy
        expect(queryByText(nonSubscriberInvitationCopy)).toBeTruthy();
    });

    test('it only renders subtitle if user is active subscriber', () => {
        // If a user subscribed, then cancelled their subscription,
        // we should not show "You are member number [#]"
        // (i.e. a user will have a subscriberNumber but not be a subscriber)
        const mockUserData = {
            ...UserProvider.defaultUserData,
            isSubscriber: false,
            subscriberNumber: 10,
        };
        const mockSubtitle = interpolate(subtitle, {
            num: mockUserData.subscriberNumber.toLocaleString(),
        });

        const { queryByText } = render(
            <UserProvider.context.Provider value={mockUserData}>
                <ThankYouPage locale="fr" />
            </UserProvider.context.Provider>
        );

        // Subtitle should not appear because isSubscriber is false
        expect(queryByText(mockSubtitle)).toBeNull();
        // Render subscriber invitations copy
        expect(queryByText(nonSubscriberInvitationCopy)).toBeTruthy();
    });

    test('it only renders subscriber invitation copy if active subscriber', () => {
        // If a user subscribed, then cancelled their subscription,
        // we should not show "You are member number [#]"
        // (i.e. a user will have a subscriberNumber but not be a subscriber)
        const mockUserData = {
            ...UserProvider.defaultUserData,
            isSubscriber: true,
            subscriberNumber: 10,
        };

        const { queryByText } = render(
            <UserProvider.context.Provider value={mockUserData}>
                <ThankYouPage />
            </UserProvider.context.Provider>
        );

        // Render subscriber invitations copy
        expect(queryByText(subscriberInvitationCopy)).toBeTruthy();
    });
});
