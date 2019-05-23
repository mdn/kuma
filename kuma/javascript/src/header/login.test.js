//@flow
import React from 'react';
import { act, create } from 'react-test-renderer';
import DocumentProvider from '../document-provider.jsx';
import { fakeDocumentData } from '../document-provider.test.js';
import Dropdown from './dropdown.jsx';
import Login from './login.jsx';
import UserProvider from '../user-provider.jsx';

test('Login snapshot before user data is fetched', () => {
    const login = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <UserProvider.context.Provider value={null}>
                <Login />
            </UserProvider.context.Provider>
        </DocumentProvider>
    ).toJSON();
    expect(login).toBe(null);
});

test('Login component when user is not logged in', () => {
    const login = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <UserProvider.context.Provider value={UserProvider.defaultUserData}>
                <Login />
            </UserProvider.context.Provider>
        </DocumentProvider>
    ).toJSON();
    expect(login.children[0]).toBe('Sign in');
    expect(login).toMatchSnapshot();
});

test('Login component when user is logged in', () => {
    const login = create(
        <DocumentProvider initialDocumentData={fakeDocumentData}>
            <UserProvider.context.Provider
                value={{
                    ...UserProvider.defaultUserData,
                    isAuthenticated: true,
                    username: 'test-username',
                    gravatarUrl: { small: 'test-url', large: 'test-bigurl' }
                }}
            >
                <Login />
            </UserProvider.context.Provider>
        </DocumentProvider>
    );

    expect(login.toJSON()).toMatchSnapshot();

    // Expect a Dropdown element
    let root = login.root;
    let dropdown = root.findByType(Dropdown);
    expect(dropdown).toBeDefined();

    // Whose label prop is an image with the expected src and alt attributes
    expect(dropdown.props.label.props.srcSet).toContain('test-url');
    expect(dropdown.props.label.props.srcSet).toContain('test-bigurl');
    expect(dropdown.props.label.props.alt).toEqual('test-username');

    // Open up the dropdown menu
    act(() => {
        login.toJSON().children[0].children[0].props.onClick();
    });

    expect(login.toJSON()).toMatchSnapshot();

    let string = JSON.stringify(login.toJSON());
    expect(string).toContain('View profile');
    expect(string).toContain('Edit profile');
    expect(string).toContain('Sign out');
});
