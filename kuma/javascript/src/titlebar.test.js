//@flow
import React from 'react';
import { create } from 'react-test-renderer';

// Must be imported before the tested file
import './__mocks__/matchMedia.js';

import { fakeDocumentData } from './document.test.js';
import Titlebar from './titlebar.jsx';
import UserProvider from './user-provider.jsx';

describe('Titlebar', () => {
    test('Titlebar displays the specified title', () => {
        let titlebar = create(
            <Titlebar title="test_title!" document={fakeDocumentData} />
        );
        let heading = titlebar.root.find(instance => instance.type === 'h1');
        expect(heading).toBeDefined();
        expect(heading.props.children).toBe('test_title!');
    });

    test('Titlebar shows edit button', () => {
        let titlebar;
        let buttons;

        // No user data; expect no buttons
        titlebar = create(
            <UserProvider.context.Provider value={null}>
                <Titlebar title="test" document={fakeDocumentData} />
            </UserProvider.context.Provider>
        );
        buttons = titlebar.root.findAll(instance => instance.type === 'button');
        expect(buttons.length).toBe(0);

        // User not logged in, expect no buttons
        titlebar = create(
            <UserProvider.context.Provider value={UserProvider.defaultUserData}>
                <Titlebar title="test" document={fakeDocumentData} />
            </UserProvider.context.Provider>
        );
        buttons = titlebar.root.findAll(instance => instance.type === 'button');
        expect(buttons.length).toBe(0);

        // User logged in and contributor, expect one button
        titlebar = create(
            <UserProvider.context.Provider
                value={{
                    ...UserProvider.defaultUserData,
                    isAuthenticated: true,
                    isContributor: true
                }}
            >
                <Titlebar
                    title="test"
                    document={{
                        ...fakeDocumentData,
                        editURL: 'foobar$edit'
                    }}
                />
            </UserProvider.context.Provider>
        );
        buttons = titlebar.root.findAll(instance => instance.type === 'button');
        expect(buttons.length).toBe(1);

        // Make the mock window.location property writeable
        // NOTE: This is a little brittle since it assumes that titlebar.jsx
        // is setting window.location and not window.location.href, for example.
        Object.defineProperty(window, 'location', {
            writable: true,
            value: null
        });

        // Clicking the button sets window.location.href to editURL
        buttons[0].props.onClick();
        expect(window.location).toBe('foobar$edit');
    });
});
