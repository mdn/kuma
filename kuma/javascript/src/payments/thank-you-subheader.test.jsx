//@flow
import React from 'react';
import { render } from '@testing-library/react';
import ThankYouSubheader, {
    title,
    subtitle,
    getSubtitle,
} from './thank-you-subheader.jsx';

describe('Thank You Subheader', () => {
    test('it renders with subscriber number', () => {
        const mockSubscriberNum = 100;
        const mockSubtitle = getSubtitle(mockSubscriberNum);
        const { queryByText } = render(
            <ThankYouSubheader subscriberNumber={mockSubscriberNum} />
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
