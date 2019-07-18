//@flow
import React from 'react';
import { act, create } from 'react-test-renderer';
import { fakeDocumentData } from './document.test.js';
import GAProvider from './ga-provider.jsx';
import { localize } from './l10n.js';
import UserProvider from './user-provider.jsx';

import TaskCompletionSurvey from './task-completion-survey.jsx';

const mockLocale = 'mock-locale';
const mockDocumentData = { ...fakeDocumentData, slug: 'mock/slug' };
const mockUserData = { ...UserProvider.defaultUserData };
const mockClientId = 'mock-client-id';
const mockGA1 = jest.fn();
const mockGA2 = function(...args) {
    if (typeof args[0] === 'function') {
        args[0]({
            get(p) {
                return p === 'clientId' ? mockClientId : '';
            }
        });
    } else {
        mockGA1(...args);
    }
};

// This is the name of the waffle flag that controls this notification
const WAFFLE_FLAG = 'sg_task_completion';

describe('TaskCompletionSurvey', () => {
    test('renders if waffle flag is set', () => {
        mockUserData.waffle.flags[WAFFLE_FLAG] = true;
        localStorage.clear();

        localize(mockLocale, {}, null);

        const tcs = create(
            <GAProvider.context.Provider value={mockGA2}>
                <UserProvider.context.Provider value={mockUserData}>
                    <TaskCompletionSurvey document={mockDocumentData} />
                </UserProvider.context.Provider>
            </GAProvider.context.Provider>
        );

        // This allows the clientId hook to run, so we get the &c= in the link
        act(() => {});
        // It should render
        expect(tcs.toJSON()).not.toBe(null);

        // The rendering should include a link
        let link = tcs.root.findByType('a');
        expect(link).toBeDefined();

        // The link href should include some things
        let href = link.props.href;
        expect(href).toContain('surveygizmo.com');
        expect(href).toContain(
            `&p=${encodeURIComponent(
                `/${mockLocale}/docs/${mockDocumentData.slug}`
            )}`
        );
        expect(href).toContain(`&c=${encodeURIComponent(mockClientId)}`);

        // Expect the GA function to have been called twice
        expect(mockGA1.mock.calls.length).toBe(2);
        expect(mockGA1.mock.calls[0]).toEqual(['set', 'dimension14', 'Yes']);
        expect(mockGA1.mock.calls[1][0]).toBe('send');
        expect(mockGA1.mock.calls[1][1].hitType).toBe('event');
        expect(mockGA1.mock.calls[1][1].eventCategory).toBe('survey');
        expect(mockGA1.mock.calls[1][1].eventAction).toBe('prompt');
        expect(mockGA1.mock.calls[1][1].eventValue).toBe('impression');
    });

    test('does not render if waffle flag is not set', () => {
        mockUserData.waffle.flags[WAFFLE_FLAG] = false;
        localStorage.clear();

        const tcs = create(
            <GAProvider.context.Provider value={mockGA2}>
                <UserProvider.context.Provider value={mockUserData}>
                    <TaskCompletionSurvey document={mockDocumentData} />
                </UserProvider.context.Provider>
            </GAProvider.context.Provider>
        );

        // It should not render anything
        expect(tcs.toJSON()).toBe(null);
    });

    test('does not render if embargoed', () => {
        mockUserData.waffle.flags[WAFFLE_FLAG] = true;
        localStorage.setItem('taskTracker', String(Date.now() + 100000));

        const tcs = create(
            <GAProvider.context.Provider value={mockGA2}>
                <UserProvider.context.Provider value={mockUserData}>
                    <TaskCompletionSurvey document={mockDocumentData} />
                </UserProvider.context.Provider>
            </GAProvider.context.Provider>
        );

        // It should not render anything
        expect(tcs.toJSON()).toBe(null);
    });

    test('does render if embargo has expired', () => {
        mockUserData.waffle.flags[WAFFLE_FLAG] = true;
        localStorage.setItem('taskTracker', String(Date.now() - 1000));

        const tcs = create(
            <GAProvider.context.Provider value={mockGA2}>
                <UserProvider.context.Provider value={mockUserData}>
                    <TaskCompletionSurvey document={mockDocumentData} />
                </UserProvider.context.Provider>
            </GAProvider.context.Provider>
        );

        // It should render something
        expect(tcs.toJSON()).not.toBe(null);
    });

    test('can be dismissed', () => {
        mockUserData.waffle.flags[WAFFLE_FLAG] = true;
        localStorage.clear();

        const tcs = create(
            <GAProvider.context.Provider value={mockGA2}>
                <UserProvider.context.Provider value={mockUserData}>
                    <TaskCompletionSurvey document={mockDocumentData} />
                </UserProvider.context.Provider>
            </GAProvider.context.Provider>
        );

        // It should render
        expect(tcs.toJSON()).not.toBe(null);

        // There is a dismiss button
        let button = tcs.root.findByType('button');

        // Simulate a click on the button
        act(() => {
            button.props.onClick();
        });

        // After clicking the button, should not be rendered
        expect(tcs.toJSON()).toBe(null);

        // And, there should be an embargo
        expect(parseInt(localStorage.getItem('taskTracker'))).toBeGreaterThan(
            Date.now()
        );
    });

    test('is dismissed and sends data to GA when the link is clicked', () => {
        mockUserData.waffle.flags[WAFFLE_FLAG] = true;
        localStorage.clear();

        const tcs = create(
            <GAProvider.context.Provider value={mockGA2}>
                <UserProvider.context.Provider value={mockUserData}>
                    <TaskCompletionSurvey document={mockDocumentData} />
                </UserProvider.context.Provider>
            </GAProvider.context.Provider>
        );

        // It should render
        expect(tcs.toJSON()).not.toBe(null);

        act(() => {});

        // Expect the GA function to have been called twice
        expect(mockGA1.mock.calls.length).toBe(2);

        // There is a link
        let link = tcs.root.findByType('a');

        // Simulate a click on the link
        act(() => {
            link.props.onClick();
        });

        // After clicking the button, should not be rendered
        expect(tcs.toJSON()).toBe(null);

        // And, there should be an embargo
        expect(parseInt(localStorage.getItem('taskTracker'))).toBeGreaterThan(
            Date.now()
        );

        // Expect the GA function to have been called another time
        expect(mockGA1.mock.calls.length).toBe(3);
        expect(mockGA1.mock.calls[2][0]).toBe('send');
        expect(mockGA1.mock.calls[2][1].hitType).toBe('event');
        expect(mockGA1.mock.calls[2][1].eventCategory).toBe('survey');
        expect(mockGA1.mock.calls[2][1].eventAction).toBe('prompt');
        expect(mockGA1.mock.calls[2][1].eventValue).toBe('participate');
    });
});
