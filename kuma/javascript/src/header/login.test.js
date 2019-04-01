//@flow
import React from 'react';
import { act, create } from 'react-test-renderer';
import CurrentUser from '../current-user.jsx';
import DocumentProvider from '../document-provider.jsx';
import { fakeDocumentData } from '../document-provider.test.js';
import Dropdown from './dropdown.jsx';
import Login from './login.jsx';

test('Login snapshot before user data is fetched', () => {
    const login = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <CurrentUser.context.Provider value={null}>
                <Login />
            </CurrentUser.context.Provider>
        </DocumentProvider>
    ).toJSON();
    expect(login).toBe(null);
});

test('Login component when user is not logged in', () => {
    const login = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <CurrentUser.context.Provider value={CurrentUser.defaultUserData}>
                <Login />
            </CurrentUser.context.Provider>
        </DocumentProvider>
    ).toJSON();
    expect(login.children[0]).toBe('Sign in');
    expect(login).toMatchSnapshot();
});

test('Login component when user is logged in', () => {
    const login = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <CurrentUser.context.Provider
                value={{
                    ...CurrentUser.defaultUserData,
                    isAuthenticated: true,
                    username: 'test-username',
                    gravatarUrl: { small: 'test-url', large: 'test-bigurl' }
                }}
            >
                <Login />
            </CurrentUser.context.Provider>
        </DocumentProvider>
    );

    expect(login.toJSON()).toMatchSnapshot();

    // Expect a edit this page link as the last one
    let root = login.root;
    let links = root.findAllByType('a');
    let link = links.pop();
    expect(link).toBeDefined();
    expect(link.props.title).toBe('Edit this page');

    // Expect a Dropdown element
    let dropdown = root.findByType(Dropdown);
    expect(dropdown).toBeDefined();

    // Whose label prop is an image with the expected src and alt attributes
    expect(dropdown.props.label.props.src).toEqual('test-url');
    expect(dropdown.props.label.props.alt).toEqual('test-username');

    // Open up the dropdown menu
    act(() => {
        login.toJSON()[0].children[0].props.onClick();
    });

    expect(login.toJSON()).toMatchSnapshot();

    let string = JSON.stringify(login.toJSON());
    expect(string).toContain('View profile');
    expect(string).toContain('Edit profile');
    expect(string).toContain('Sign out');
});
