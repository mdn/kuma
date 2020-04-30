import React from 'react';
import { fireEvent, render } from '@testing-library/react';
import {
    toBeInTheDocument,
    toHaveClass,
} from '@testing-library/jest-dom/matchers';
import GAProvider from './ga-provider.jsx';
import Breadcrumbs from './breadcrumbs.jsx';

expect.extend({ toBeInTheDocument, toHaveClass });

describe('Breadcrumbs', () => {
    const mockDocumentData = {
        // url needs a # to trick it into thinking it's a hash change:
        // JSDOM error - `Not implemented: navigation (except hash changes)`
        absoluteURL: '#main-url',
        title: 'main crumb',
        parents: [
            {
                title: 'crumb 1',
                url: '/url-1',
            },
            {
                title: 'crumb 2',
                url: '/url-2',
            },
            {
                title: 'crumb 3',
                url: '/url-3',
            },
        ],
    };

    it('renders correct number of crumbs (parents + current page)', () => {
        const expected = mockDocumentData.parents.length + 1;
        const { queryAllByText } = render(
            <Breadcrumbs document={mockDocumentData} />
        );
        const items = queryAllByText(/crumb/);
        expect(items).toHaveLength(expected);
    });

    it('gives the last parent a different class name, so we can style it differently for small screens', () => {
        const expected = 'breadcrumb-chevron';
        const firstParent = mockDocumentData.parents[0];
        const lastParent =
            mockDocumentData.parents[mockDocumentData.parents.length - 1];
        const { queryByText } = render(
            <Breadcrumbs document={mockDocumentData} />
        );
        const firstElement = queryByText(firstParent.title).closest('a');
        const lastElement = queryByText(lastParent.title).closest('a');

        expect(firstElement).toHaveClass(expected);
        expect(lastElement).not.toHaveClass(expected);
    });

    it('logs GA event for every crumb click', () => {
        const mockGA = jest.fn();
        const { queryByText } = render(
            <GAProvider.context.Provider value={mockGA}>
                <Breadcrumbs document={mockDocumentData} />
            </GAProvider.context.Provider>
        );

        // click on current crumb
        fireEvent.click(queryByText(mockDocumentData.title).closest('a'));

        // check that our GA event was called
        expect(mockGA).toHaveBeenCalledWith('send', {
            eventAction: 'Crumbs',
            eventCategory: 'Wiki',
            eventLabel: `${location.href}${mockDocumentData.absoluteURL}`,
            hitType: 'event',
        });
    });
});
