//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import Titlebar from './titlebar.jsx';
import UserProvider from './user-provider.jsx';

export const fakeDocumentData = {
    locale: 'en-US',
    slug: 'test',
    enSlug: 'fake/en/slug',
    id: 42,
    title: '[fake document title]',
    summary: '[fake document summary]',
    language: 'English (US)',
    hrefLang: 'en',
    absoluteURL: '[fake absolute url]',
    editURL: '[fake edit url]',
    bodyHTML: '[fake body HTML]',
    quickLinksHTML: '[fake quicklinks HTML]',
    tocHTML: '[fake TOC HTML]',
    parents: [
        {
            url: '[fake grandparent url]',
            title: '[fake grandparent title]'
        },
        {
            url: '[fake parent url]',
            title: '[fake parent title]'
        }
    ],
    translations: [
        {
            locale: 'es',
            language: 'Español',
            hrefLang: 'es',
            localizedLanguage: 'Spanish',
            url: '[fake spanish url]',
            title: '[fake spanish translation]'
        }
    ],
    contributors: ['mike', 'ike'],
    lastModified: '2019-01-02T03:04:05Z',
    lastModifiedBy: 'ike'
};

describe('Titlebar', () => {
    test('Titlebar displays the specified title', () => {
        let titlebar = create(
            <Titlebar title="test_title!" document={fakeDocumentData} />
        );
        let heading = titlebar.root.find(instance => instance.type === 'h1');
        expect(heading).toBeDefined();
        expect(heading.props.children).toBe('test_title!');
    });

    test('Titlebar shows edit and history buttons', () => {
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
                    title="test"
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
        // NOTE: This is a little brittle since it assumes that titlebar.jsx
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
});
