//@flow
import React from 'react';
import { act, create } from 'react-test-renderer';
import ActiveBanner, {
    DEVELOPER_NEEDS_ID,
    SUBSCRIPTION_ID
} from './active-banner.jsx';
import UserProvider from './user-provider.jsx';

const mockUserData = { ...UserProvider.defaultUserData };

describe('ActiveBanner', () => {
    beforeEach(() => {
        localStorage.clear();
    });

    test('renders nothing if no waffle flags set', () => {
        expect(
            create(
                <UserProvider.context.Provider value={mockUserData}>
                    <ActiveBanner />
                </UserProvider.context.Provider>
            ).toJSON()
        ).toBe(null);
    });

    test('renders banners when their waffle flags are set', () => {
        mockUserData.waffle.flags = { [DEVELOPER_NEEDS_ID]: true };
        expect(
            JSON.stringify(
                create(
                    <UserProvider.context.Provider value={mockUserData}>
                        <ActiveBanner />
                    </UserProvider.context.Provider>
                ).toJSON()
            )
        ).toContain(DEVELOPER_NEEDS_ID);
    });

    test('renders banner for logged in users', () => {
        mockUserData.isAuthenticated = true;
        mockUserData.waffle.flags = {
            [SUBSCRIPTION_ID]: true
        };

        expect(
            JSON.stringify(
                create(
                    <UserProvider.context.Provider value={mockUserData}>
                        <ActiveBanner />
                    </UserProvider.context.Provider>
                ).toJSON()
            )
        ).toContain(SUBSCRIPTION_ID);
    });

    test('renders nothing if user not logged in', () => {
        mockUserData.isAuthenticated = false;
        mockUserData.waffle.flags = {
            [SUBSCRIPTION_ID]: true
        };

        expect(
            create(
                <UserProvider.context.Provider value={mockUserData}>
                    <ActiveBanner />
                </UserProvider.context.Provider>
            ).toJSON()
        ).toBe(null);
    });

    test('renders first banner and not second when both flags are set', () => {
        mockUserData.waffle.flags = {
            [DEVELOPER_NEEDS_ID]: true,
            [SUBSCRIPTION_ID]: true
        };
        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        let snapshot = JSON.stringify(banner.toJSON());
        expect(snapshot).toContain(DEVELOPER_NEEDS_ID);
        expect(snapshot).not.toContain(SUBSCRIPTION_ID);
    });

    test('renders second active banner if first is embargoed', () => {
        mockUserData.isAuthenticated = true;
        mockUserData.waffle.flags = {
            [DEVELOPER_NEEDS_ID]: true,
            [SUBSCRIPTION_ID]: true
        };

        localStorage.setItem(
            `banner.${DEVELOPER_NEEDS_ID}.embargoed_until`,
            String(Date.now() + 10000)
        );

        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        let snapshot = JSON.stringify(banner.toJSON());
        expect(snapshot).not.toContain(DEVELOPER_NEEDS_ID);
        expect(snapshot).toContain(SUBSCRIPTION_ID);
    });

    test('renders nothing if all active banners are embargoed', () => {
        mockUserData.waffle.flags = {
            [DEVELOPER_NEEDS_ID]: true,
            [SUBSCRIPTION_ID]: true
        };

        localStorage.setItem(
            `banner.${DEVELOPER_NEEDS_ID}.embargoed_until`,
            String(Date.now() + 10000)
        );
        localStorage.setItem(
            `banner.${SUBSCRIPTION_ID}.embargoed_until`,
            String(Date.now() + 10000)
        );

        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        expect(banner.toJSON()).toBe(null);
    });

    test('embargos expire', () => {
        mockUserData.isAuthenticated = true;
        mockUserData.waffle.flags = {
            [DEVELOPER_NEEDS_ID]: true,
            [SUBSCRIPTION_ID]: true
        };

        localStorage.setItem(
            `banner.${DEVELOPER_NEEDS_ID}.embargoed_until`,
            String(Date.now() + 10000)
        );
        localStorage.setItem(
            `banner.${SUBSCRIPTION_ID}.embargoed_until`,
            String(Date.now() - 1)
        );

        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        let snapshot = JSON.stringify(banner.toJSON());
        expect(snapshot).toContain(SUBSCRIPTION_ID);

        localStorage.setItem(
            `banner.${DEVELOPER_NEEDS_ID}.embargoed_until`,
            String(Date.now() - 1)
        );

        banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        snapshot = JSON.stringify(banner.toJSON());
        expect(snapshot).toContain(DEVELOPER_NEEDS_ID);
    });

    test('banners can be dismissed', () => {
        mockUserData.isAuthenticated = true;
        mockUserData.waffle.flags = {
            [DEVELOPER_NEEDS_ID]: true,
            [SUBSCRIPTION_ID]: true
        };
        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        expect(JSON.stringify(banner.toJSON())).toContain(DEVELOPER_NEEDS_ID);

        let button = banner.root.findByType('button');
        expect(button).toBeDefined();

        act(() => {
            // Simulate a click on the dismiss button
            button.props.onClick();
        });

        // Now that it is dismissed expect to render null
        expect(banner.toJSON()).toBe(null);

        // Re-render and expect the second banner
        banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        expect(JSON.stringify(banner.toJSON())).toContain(SUBSCRIPTION_ID);

        // Dismiss the second banner
        button = banner.root.findByType('button');
        act(() => {
            // Simulate a click on the dismiss button
            button.props.onClick();
        });

        // Now that it is dismissed expect to render null
        expect(banner.toJSON()).toBe(null);

        // Do one final re-render and expect null since both are embargoed
        banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        expect(banner.toJSON()).toBe(null);
    });

    test('adds target and rel for banners set to open in new window', () => {
        mockUserData.isAuthenticated = false;
        mockUserData.waffle.flags = {
            [DEVELOPER_NEEDS_ID]: true
        };

        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        let ctaButtonProps = banner.root.findByProps({
            className: 'mdn-cta-button'
        }).props;

        expect(JSON.stringify(banner.toJSON())).toContain(DEVELOPER_NEEDS_ID);
        expect(ctaButtonProps.target).toBeDefined();
        expect(ctaButtonProps.rel).toBeDefined();
    });

    test('does not add target and rel for default banners', () => {
        mockUserData.isAuthenticated = true;
        mockUserData.waffle.flags = {
            [SUBSCRIPTION_ID]: true
        };

        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        let ctaButtonProps = banner.root.findByProps({
            className: 'mdn-cta-button'
        }).props;

        expect(ctaButtonProps.target).not.toBeDefined();
        expect(ctaButtonProps.rel).not.toBeDefined();
    });
});
