//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import Dropdown from './dropdown.jsx';
import Login from './login.jsx';
import UserProvider from '../user-provider.jsx';

test('Login snapshot before user data is fetched', () => {
    const login = create(
        <UserProvider.context.Provider value={null}>
            <Login />
        </UserProvider.context.Provider>
    ).toJSON();
    expect(login).toBe(null);
});

test('Login component when user is not logged in', () => {
    const login = create(
        <UserProvider.context.Provider value={UserProvider.defaultUserData}>
            <Login />
        </UserProvider.context.Provider>
    ).toJSON();
    expect(login.children[0]).toBe('Sign in');
    expect(login).toMatchSnapshot();
});

test('Login component when user is logged in', () => {
    const login = create(
        <UserProvider.context.Provider
            value={{
                ...UserProvider.defaultUserData,
                isAuthenticated: true,
                username: 'test-username',
                avatarUrl: 'test-url',
            }}
        >
            <Login />
        </UserProvider.context.Provider>
    );

    expect(login.toJSON()).toMatchSnapshot();

    // Expect a Dropdown element
    let root = login.root;
    let dropdown = root.findByType(Dropdown);

    expect(dropdown).toBeDefined();

    // Whose label prop is an image with the expected src
    expect(dropdown.props.label.props.src).toContain('test-url');

    let string = JSON.stringify(login.toJSON());
    expect(string).toContain('View profile');
    expect(string).toContain('Edit profile');
    expect(string).toContain('Sign out');
});
