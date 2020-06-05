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
    let dropDownLabelProps = dropdown.props.label.props.children[0].props;
    expect(dropdown).toBeDefined();

    // Whose label prop is an image with the expected src and alt attributes
    expect(dropDownLabelProps.src).toContain('test-url');
    expect(dropDownLabelProps.alt).toEqual('test-username');

    let string = JSON.stringify(login.toJSON());
    expect(string).not.toContain('Contributions');
    expect(string).toContain('View profile');
    expect(string).toContain('Edit profile');
    expect(string).toContain('Sign out');
});

test('Login component when user is logged in and has wiki contributions', () => {
    const login = create(
        <UserProvider.context.Provider
            value={{
                ...UserProvider.defaultUserData,
                isAuthenticated: true,
                username: 'test-username',
                avatarUrl: 'test-url',
                wikiContributions: 1,
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

    let string = JSON.stringify(login.toJSON());
    expect(string).toContain('Contributions');
    expect(string).toContain('View profile');
    expect(string).toContain('Edit profile');
    expect(string).toContain('Sign out');
});
