import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import { toBeInTheDocument } from '@testing-library/jest-dom/matchers';
import { GenericError, ErrorComponent } from './errors.jsx';

expect.extend({ toBeInTheDocument });

describe('ErrorComponent', () => {
    it('renders text and no button', () => {
        const mockProps = {
            text: 'An explanation for why we are sorry.',
        };
        const { queryByText } = render(<ErrorComponent {...mockProps} />);

        expect(queryByText(mockProps.text)).toBeInTheDocument();
        expect(queryByText(/try again/i)).not.toBeInTheDocument();
    });

    it('renders text and a functioning button', () => {
        const mockProps = {
            text: 'More reasons why we are sorry.',
            onClick: jest.fn(),
        };
        const { queryByText } = render(<ErrorComponent {...mockProps} />);
        const button = queryByText(/try again/i);

        fireEvent.click(button);

        expect(queryByText(mockProps.text)).toBeInTheDocument();
        expect(mockProps.onClick).toHaveBeenCalled();
    });
});

describe('Generic message', () => {
    it('renders generic error message if no text was provided', () => {
        window.mdn = {
            contributionSupportEmail: 'mock-support@mozilla.com',
        };
        const { queryByText } = render(<GenericError />);

        expect(queryByText(/something went wrong/)).toBeInTheDocument();
        expect(
            queryByText(window.mdn.contributionSupportEmail)
        ).toBeInTheDocument();
    });
});
