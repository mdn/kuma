//@flow
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import {
    toBeInTheDocument,
    toHaveClass,
} from '@testing-library/jest-dom/matchers';

expect.extend({ toBeInTheDocument, toHaveClass });

import Search from './search.jsx';

const setup = (mockQuery = '') => {
    render(<Search initialQuery={mockQuery} />);

    const form = screen.getByRole('search');
    const input = screen.getByLabelText('Search MDN');
    const openButton = screen.queryByRole('button', {
        name: /open search/i,
    });

    return {
        form,
        input,
        openButton,
    };
};

describe('Search form', () => {
    it('renders default state', () => {
        const { form, openButton } = setup();

        // search form
        expect(form).toBeInTheDocument();

        // open search button
        expect(openButton).toBeInTheDocument();
    });

    it('populates search field with existing query', () => {
        const mockQuery = 'fake search';
        const { input } = setup(mockQuery);
        expect(input.value).toBe(mockQuery);
    });

    it('toggles form styles when button is clicked', () => {
        const { form, openButton } = setup();
        const expectedClassName = 'show-form';

        // no show form class name by default
        expect(form.parentElement).not.toHaveClass(expectedClassName);

        fireEvent.click(openButton);

        const closeButton = screen.queryByRole('button', {
            name: /close search/i,
        });

        // close button shows, open button is gone, classname is applied
        expect(closeButton).toBeInTheDocument;
        expect(openButton).not.toBeInTheDocument;
        expect(form.parentElement).toHaveClass(expectedClassName);

        fireEvent.click(closeButton);

        // default state is restored:
        // close button is gone, open button shows, form has no class name
        expect(closeButton).not.toBeInTheDocument;
        expect(openButton).toBeInTheDocument;
        expect(form.parentElement).not.toHaveClass(expectedClassName);
    });

    it('clears search input when close button is clicked', () => {
        const { openButton, input } = setup();
        const mockValue = 'mock value';

        fireEvent.click(openButton);

        fireEvent.change(input, { target: { value: mockValue } });

        expect(input.value).toBe(mockValue);

        const closeButton = screen.getByRole('button', {
            name: /close search/i,
        });

        fireEvent.click(closeButton);

        expect(input.value).toBe('');
    });
});
