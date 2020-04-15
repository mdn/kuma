import React from 'react';
import { cleanup, render } from '@testing-library/react';
import { toBeInTheDocument } from '@testing-library/jest-dom/matchers';
import Page from './page.jsx';

expect.extend({ toBeInTheDocument });

describe('Page', () => {
    afterEach(() => {
        cleanup();
    });

    it('renders a11y nav, header, and footer', () => {
        const { queryByTestId } = render(<Page>hello</Page>);
        expect(queryByTestId('a11y-nav')).toBeInTheDocument();
        expect(queryByTestId('header')).toBeInTheDocument();
        expect(queryByTestId('footer')).toBeInTheDocument();
    });

    it('renders children', () => {
        const expectedChild = 'i am a child';
        const { queryByText } = render(<Page>{expectedChild}</Page>);
        expect(queryByText(expectedChild)).toBeInTheDocument();
    });
});
