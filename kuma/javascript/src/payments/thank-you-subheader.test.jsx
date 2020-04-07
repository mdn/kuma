//@flow
import React from 'react';
import { render } from '@testing-library/react';
import ThankYouSubheader from './thank-you-subheader.jsx';
import { strings, getMemberNumberString } from './strings.js';

describe('Thank You Subheader', () => {
    test('it renders with subscriber number', () => {
        const mockSubscriberNum = 100;
        const mockIsSubscriber = true;
        const mockSubtitle = getMemberNumberString(
            mockSubscriberNum,
            mockIsSubscriber
        );
        const { queryByText } = render(
            <ThankYouSubheader
                subscriberNumber={mockSubscriberNum}
                isSubscriber={mockIsSubscriber}
            />
        );

        // Title
        expect(queryByText(strings.thankYou)).toBeTruthy();

        // Subtitle with member number
        expect(queryByText(mockSubtitle)).toBeTruthy();
    });

    test('it renders only the title if no subscriber number is provided', () => {
        const { queryByText } = render(
            <ThankYouSubheader subscriberNumber={null} />
        );

        // Title
        expect(queryByText(strings.thankYou)).toBeTruthy();

        // Subtitle should not render
        expect(queryByText(strings.memberNum)).toBeNull();
    });
});
