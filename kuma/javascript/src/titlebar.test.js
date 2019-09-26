//@flow
import React from 'react';
import { create } from 'react-test-renderer';

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

    test('Titlebar shows edit in wiki link', () => {
        let titlebar;
        let editLink;

        // No user data; expect no buttons
        titlebar = create(
            <UserProvider.context.Provider value={null}>
                <Titlebar title="test" document={fakeDocumentData} />
            </UserProvider.context.Provider>
        );
        editLink = titlebar.root.findAll(instance => instance.type === 'a');
        expect(editLink.length).toBe(0);

        // User not logged in, expect no buttons
        titlebar = create(
            <UserProvider.context.Provider value={UserProvider.defaultUserData}>
                <Titlebar title="test" document={fakeDocumentData} />
            </UserProvider.context.Provider>
        );
        editLink = titlebar.root.findAll(instance => instance.type === 'a');
        expect(editLink.length).toBe(0);

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
                        wikiURL: 'foobar'
                    }}
                />
            </UserProvider.context.Provider>
        );
        editLink = titlebar.root.findAll(instance => instance.type === 'a');
        expect(editLink.length).toBe(1);
        expect(editLink[0].props.href).toBe('foobar');
    });
});
