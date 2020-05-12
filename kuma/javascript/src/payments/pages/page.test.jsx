import React from 'react';
import { render } from '@testing-library/react';
import Page from './page.jsx';

describe('Page', () => {
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
