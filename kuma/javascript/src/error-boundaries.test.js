import React from 'react';
import { create } from 'react-test-renderer';
import { AppErrorBoundary, ContentErrorBoundary } from './error-boundaries.jsx';

describe('AppErrorBoundary component', () => {
    test('rendering without errors', () => {
        const page = create(
            <AppErrorBoundary>
                <p>Anything</p>
            </AppErrorBoundary>
        );
        const snapshot = JSON.stringify(page.toJSON());
        expect(snapshot).toContain('Anything');
    });
    test('rendering with errors', () => {
        function BadComponent() {
            throw new Error('badness');
        }

        const originalError = console.error;
        console.error = jest.fn();

        const page = create(
            <AppErrorBoundary>
                <div>
                    <BadComponent />
                    <p>Anything</p>
                </div>
            </AppErrorBoundary>
        );
        console.error = originalError;
        const snapshot = JSON.stringify(page.toJSON(), null, 2);
        expect(snapshot).not.toContain('Anything');
        expect(snapshot).toContain('Application rendering error');
    });
});

describe('ContentErrorBoundary component', () => {
    test('rendering without errors', () => {
        const page = create(
            <ContentErrorBoundary>
                <p>Anything</p>
            </ContentErrorBoundary>
        );
        const snapshot = JSON.stringify(page.toJSON());
        expect(snapshot).toContain('Anything');
    });
    test('rendering with errors', () => {
        function BadComponent() {
            throw new Error('badness');
        }

        const originalError = console.error;
        console.error = jest.fn();

        const page = create(
            <ContentErrorBoundary>
                <div>
                    <BadComponent />
                    <p>Anything</p>
                </div>
            </ContentErrorBoundary>
        );
        console.error = originalError;
        const snapshot = JSON.stringify(page.toJSON(), null, 2);
        expect(snapshot).not.toContain('Anything');
        expect(snapshot).toContain('Content rendering error');
    });
});
