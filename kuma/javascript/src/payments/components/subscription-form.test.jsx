import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react';
import SubscriptionForm, {
    STRIPE_CONTINUE_SESSIONSTORAGE_KEY,
} from './subscription-form.jsx';
import GAProvider from '../../ga-provider.jsx';
import UserProvider from '../../user-provider.jsx';
import useScriptLoading from './use-script-loading.js';

jest.mock('./use-script-loading.js');

describe('When submitting Subscription Form', () => {
    beforeAll(() => {
        useScriptLoading.mockReturnValue([
            Promise.resolve('success'),
            () => null,
        ]);

        // if this is not in beforeAll, it triggers this console.error:
        // JSDom Error: Not implemented: navigation (except hash changes)
        delete window.location;
        window.location = {
            assign: jest.fn(),
            pathname: `/mock-path/`,
        };
    });

    it('renders initial form', () => {
        const { queryByTestId, queryByText } = render(<SubscriptionForm />);
        expect(queryByText('$5')).toBeInTheDocument();
        expect(queryByTestId('subscription-form')).toBeInTheDocument();
    });

    it('records GA events', () => {
        const mockGA = jest.fn();
        const { queryByText } = render(
            <GAProvider.context.Provider value={mockGA}>
                <SubscriptionForm />
            </GAProvider.context.Provider>
        );

        fireEvent.click(queryByText(/Continue/));

        expect(mockGA).toHaveBeenCalledWith('send', {
            eventAction: 'subscribe intent (unauthenticated)',
            eventCategory: 'monthly payments',
            eventLabel: 'subscription-landing-page',
            hitType: 'event',
        });
        expect(mockGA).toHaveBeenCalledWith('send', {
            eventAction: 'subscribe intent',
            eventCategory: 'monthly payments',
            eventLabel: 'subscription-landing-page',
            hitType: 'event',
        });
    });

    it('redirects to sign-in page if user is not logged in and sign-in modal is not available', () => {
        const { queryByText } = render(<SubscriptionForm />);

        fireEvent.click(queryByText(/Continue/));

        expect(window.location.assign).toHaveBeenCalledWith(
            `/en-US/users/account/signup-landing?next=%2Fmock-path%2F`
        );
    });

    it('shows sign-in modal if user is not logged in and modal  _is_ available', () => {
        window.mdn = {
            triggerAuthModal: jest.fn(),
        };

        delete window.sessionStorage;
        window.sessionStorage = {
            setItem: jest.fn(),
        };

        const { queryByText } = render(<SubscriptionForm />);

        fireEvent.click(queryByText(/Continue/));

        expect(window.sessionStorage.setItem).toHaveBeenCalledWith(
            STRIPE_CONTINUE_SESSIONSTORAGE_KEY,
            'true'
        );
        expect(window.mdn.triggerAuthModal).toHaveBeenCalled();
    });

    it('shows error message if Stripe cannot load', async () => {
        const mockReloadStripe = jest.fn();

        // mock failed script loading
        useScriptLoading.mockReturnValue([
            Promise.reject({ ok: false }),
            mockReloadStripe,
        ]);

        const { queryByText } = render(<SubscriptionForm />);

        await waitFor(() => {
            expect(
                queryByText(
                    /an error happened trying to load the Stripe integration/i
                )
            ).toBeInTheDocument();
        });

        // Click on "Try again" button
        fireEvent.click(queryByText(/try again/i));

        expect(mockReloadStripe).toHaveBeenCalled();
    });

    it('shows Stripe modal if user is logged in', async () => {
        window.mdn = {
            stripePublicKey: 'mock-key-123',
        };

        const expectedConfig = {
            amount: 500,
            closed: expect.any(Function),
            currency: 'usd',
            email: null,
            key: window.mdn.stripePublicKey,
            locale: 'en-US',
            name: 'MDN Web Docs',
            token: expect.any(Function),
            zipCode: true,
        };

        // Mock StripeCheckout
        const stripeConfigureMock = {
            open: jest.fn(),
            close: jest.fn(),
        };

        window.StripeCheckout = {
            configure: jest.fn().mockReturnValue(stripeConfigureMock),
        };

        useScriptLoading.mockReturnValue([
            Promise.resolve('success'),
            () => null,
        ]);

        const mockUserData = {
            ...UserProvider.defaultUserData,
            isAuthenticated: true,
        };

        const { queryByText } = render(
            <UserProvider.context.Provider value={mockUserData}>
                <SubscriptionForm />
            </UserProvider.context.Provider>
        );

        fireEvent.click(queryByText(/Continue/));

        // Check that stripeHandler.open() was called
        await waitFor(() => {
            expect(window.StripeCheckout.configure).toHaveBeenCalledWith(
                expectedConfig
            );
            expect(stripeConfigureMock.open).toHaveBeenCalled();
        });
    });
});
