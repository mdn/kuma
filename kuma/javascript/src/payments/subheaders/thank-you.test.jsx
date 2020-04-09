//@flow
import React from 'react';
import { render } from '@testing-library/react';
import ThankYouSubheader, { title, subtitle } from './thank-you.jsx';
import { interpolate } from '../../l10n.js';

describe('Thank You Subheader', () => {
    test('it renders with subscriber number', () => {
        const mockSubscriberNum = 100;
        const mockSubtitle = interpolate(subtitle, {
            num: mockSubscriberNum.toLocaleString(),
        });
        const { queryByText } = render(
            <ThankYouSubheader num={mockSubscriberNum} />
        );

        // Title
        expect(queryByText(title)).toBeTruthy();

        // Subtitle with member number
        expect(queryByText(mockSubtitle)).toBeTruthy();
    });

    test('it renders only the title if no subscriber number is provided', () => {
        const { queryByText } = render(
            <ThankYouSubheader subscriberNumber={null} />
        );

        // Title
        expect(queryByText(title)).toBeTruthy();

        // Subtitle should not render
        expect(queryByText(subtitle)).toBeNull();
    });
});
