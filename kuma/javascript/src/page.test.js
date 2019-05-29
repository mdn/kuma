//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import DocumentProvider from './document-provider.jsx';
import { fakeDocumentData } from './document-provider.test.js';
import Page from './page.jsx';
import { Titlebar } from './page.jsx';
import UserProvider from './user-provider.jsx';

test('Page snapshot', () => {
    const page = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <Page />
        </DocumentProvider>
    );
    expect(page.toJSON()).toMatchSnapshot();
});

test('Titlebar shows edit and history buttons', () => {
    let titlebar;
    let buttons;

    // No user data; expect no buttons
    titlebar = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <UserProvider.context.Provider value={null}>
                <Titlebar document={fakeDocumentData} />
            </UserProvider.context.Provider>
        </DocumentProvider>
    );
    buttons = titlebar.root.findAll(instance => instance.type === 'button');
    expect(buttons.length).toBe(0);

    // User not logged in, expect no buttons
    titlebar = create(
        <UserProvider.context.Provider value={UserProvider.defaultUserData}>
            <Titlebar document={fakeDocumentData} />
        </UserProvider.context.Provider>
    );
    buttons = titlebar.root.findAll(instance => instance.type === 'button');
    expect(buttons.length).toBe(0);

    // User logged in and contributor, expect two buttons
    titlebar = create(
        <UserProvider.context.Provider
            value={{
                ...UserProvider.defaultUserData,
                isAuthenticated: true,
                isContributor: true
            }}
        >
            <Titlebar
                document={{
                    ...fakeDocumentData,
                    editURL: 'foobar$edit'
                }}
            />
        </UserProvider.context.Provider>
    );
    buttons = titlebar.root.findAll(instance => instance.type === 'button');
    expect(buttons.length).toBe(2);

    // Make the mock window.location property writeable
    // NOTE: This is a little brittle since it assumes that page.jsx
    // is setting window.location and not window.location.href, for example.
    Object.defineProperty(window, 'location', {
        writable: true,
        value: null
    });

    // Clicking first button sets window.location.href to editURL
    // Clicking the second button sets it to the history URL instead
    buttons[0].props.onClick();
    expect(window.location).toBe('foobar$edit');
    buttons[1].props.onClick();
    expect(window.location).toBe('foobar$history');
});
