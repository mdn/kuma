import React from 'react';
import { create } from 'react-test-renderer';

import App from './app.jsx';
import SinglePageApp from './single-page-app.jsx';
import LandingPage from './landing-page.jsx';
import SignupFlow from './signup-flow.jsx';
import UserAccount from './user-account/user-account.jsx';

import { fakeDocumentData } from './document.test.js';

let mockData = {
    documentData: fakeDocumentData,
    url: 'mock-url'
};

jest.mock('./single-page-app', () => '<single-page-app />');
jest.mock('./landing-page', () => '<landing-page />');
jest.mock('./signup-flow', () => '<signup-flow />');
jest.mock('./user-account/user-account', () => '<user-account />');

describe('App', () => {
    test('throws an Error when the componentName is unknown', () => {
        const originalError = console.error;
        console.error = jest.fn();

        expect(() => {
            create(
                <App componentName="UNKNOWN_COMPONENT_NAME" data={mockData} />
            );
        }).toThrowError(
            /Cannot render or hydrate unknown component: UNKNOWN_COMPONENT_NAME/
        );

        console.error = originalError;
    });

    test('renders SinglePageApp when the componentName is SPA', () => {
        let app = create(<App componentName="SPA" data={mockData} />);

        const { root } = app;
        expect(root.findAllByType(SinglePageApp).length).toBe(1);
    });

    test('renders LandingPage when the componentName is landing', () => {
        let app = create(<App componentName="landing" data={mockData} />);

        const { root } = app;
        expect(root.findAllByType(LandingPage).length).toBe(1);
    });

    it('renders SignupFlow when componentName is signupflow', () => {
        let app = create(<App componentName="signupflow" data={mockData} />);

        const { root } = app;
        expect(root.findAllByType(SignupFlow).length).toBe(1);
    });

    it('renders a UserAccount when componentName is user-account', () => {
        let app = create(<App componentName="user-account" data={mockData} />);

        const { root } = app;
        expect(root.findAllByType(UserAccount).length).toBe(1);
    });
});
