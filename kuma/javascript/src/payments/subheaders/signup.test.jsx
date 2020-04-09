//@flow
import React from 'react';
import { render } from '@testing-library/react';
import SignupSubheader, { title, subtitle, description } from './signup.jsx';
import { interpolate } from '../../l10n.js';

describe('Signup Subheader', () => {
    it('renders with correct content', () => {
        const mockProps = {
            num: 101,
            showSubscriptionForm: false,
        };
        const mockSubtitle = interpolate(subtitle, {
            num: mockProps.num.toLocaleString(),
        });
        const mockDescription = interpolate(description, {
            amount: '$5',
        });

        const { queryByText, queryByTestId } = render(
            <SignupSubheader {...mockProps} />
        );

        // Title
        expect(queryByText(title)).toBeTruthy();

        // Subtitle with potential member number
        expect(queryByText(mockSubtitle)).toBeTruthy();

        // Description
        expect(queryByText(mockDescription)).toBeTruthy();

        // Subscription form should not render
        expect(queryByTestId('subscription-form')).toBeNull();
    });

    it('renders subscription form', () => {
        const { queryByTestId } = render(
            <SignupSubheader num={101} showSubscriptionForm />
        );

        // Subscription form renders
        expect(queryByTestId('subscription-form')).toBeTruthy();
    });
});
