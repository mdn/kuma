//@flow
import React from 'react';
import { act, create } from 'react-test-renderer';
import ActiveBanner, { COMMON_SURVEY_ID } from './active-banner.jsx';
import UserProvider from './user-provider.jsx';

describe('ActiveBanner', () => {
    let mockUserData;
    beforeEach(() => {
        localStorage.clear();
        mockUserData = { ...UserProvider.defaultUserData };
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
        mockUserData.waffle.flags = { [COMMON_SURVEY_ID]: true };
        expect(
            JSON.stringify(
                create(
                    <UserProvider.context.Provider value={mockUserData}>
                        <ActiveBanner />
                    </UserProvider.context.Provider>
                ).toJSON()
            )
        ).toContain(COMMON_SURVEY_ID);
    });

    test('renders second active banner if first is embargoed', () => {
        mockUserData.isAuthenticated = true;
        mockUserData.waffle.flags = {
            [COMMON_SURVEY_ID]: true,
        };

        localStorage.setItem(
            `banner.${COMMON_SURVEY_ID}.embargoed_until`,
            String(Date.now() + 10000)
        );

        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        let snapshot = JSON.stringify(banner.toJSON());
        expect(snapshot).not.toContain(COMMON_SURVEY_ID);
    });

    test('renders nothing if all active banners are embargoed', () => {
        mockUserData.waffle.flags = {
            [COMMON_SURVEY_ID]: true,
        };

        localStorage.setItem(
            `banner.${COMMON_SURVEY_ID}.embargoed_until`,
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
            [COMMON_SURVEY_ID]: true,
        };

        localStorage.setItem(
            `banner.${COMMON_SURVEY_ID}.embargoed_until`,
            String(Date.now() + 10000)
        );

        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        let snapshot = JSON.stringify(banner.toJSON());

        localStorage.setItem(
            `banner.${COMMON_SURVEY_ID}.embargoed_until`,
            String(Date.now() - 1)
        );

        banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        snapshot = JSON.stringify(banner.toJSON());
        expect(snapshot).toContain(COMMON_SURVEY_ID);
    });

    test('banners can be dismissed', () => {
        mockUserData.isAuthenticated = true;
        mockUserData.waffle.switches = {
            [COMMON_SURVEY_ID]: true,
        };
        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        expect(JSON.stringify(banner.toJSON())).toContain(COMMON_SURVEY_ID);

        let button = banner.root.findByType('button');
        expect(button).toBeDefined();

        act(() => {
            // Simulate a click on the dismiss button
            button.props.onClick();
        });

        // Now that it is dismissed expect to render null
        expect(banner.toJSON()).toBe(null);
    });

    test('adds target and rel for banners set to open in new window', () => {
        mockUserData.isAuthenticated = false;
        mockUserData.waffle.switches = {
            [COMMON_SURVEY_ID]: true,
        };

        let banner = create(
            <UserProvider.context.Provider value={mockUserData}>
                <ActiveBanner />
            </UserProvider.context.Provider>
        );

        let ctaButtonProps = banner.root.findByProps({
            className: 'button light',
        }).props;

        expect(JSON.stringify(banner.toJSON())).toContain(COMMON_SURVEY_ID);
        expect(ctaButtonProps.target).toBeDefined();
        expect(ctaButtonProps.rel).toBeDefined();
    });
});
