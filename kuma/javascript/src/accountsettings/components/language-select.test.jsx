import React from 'react';
import { render, screen } from '@testing-library/react';

import LanguageSelect from './language-select.jsx';

const label = 'Testing';
const name = 'test-name';

const getProps = (label, name, defaultValue = 'en-US') => {
    return {
        defaultValue,
        label,
        name,
        sortedLanguages: {
            'en-US': 'English (US)',
            'en-GB': 'English (UK)',
            fr: 'French',
            de: 'German',
        },
    };
};

describe('LanguageSelector', () => {
    it('returns langauge select with appropriate label element', () => {
        render(<LanguageSelect {...getProps(label, name)} />);

        const fieldLabel = screen.getByText(label);

        expect(fieldLabel).toHaveTextContent(label);
        expect(fieldLabel).toHaveAttribute(
            'for',
            expect.stringContaining(name)
        );
    });

    it('returns langauge select with appropriate select element', () => {
        render(<LanguageSelect {...getProps(label, name)} />);

        /*
         * Being able to get the select element via the label text also
         * confirms that our label is correctly associated with the
         * select element.
         */
        const langSelect = screen.getByLabelText(label);

        expect(langSelect).toHaveAttribute('id', expect.stringContaining(name));
        expect(langSelect).toHaveAttribute(
            'name',
            expect.stringContaining(name)
        );
        expect(langSelect).toHaveValue('en-US');
    });

    it('returns langauge select with appropriate selected value', () => {
        render(<LanguageSelect {...getProps(label, name, 'fr')} />);

        const langSelect = screen.getByLabelText(label);

        expect(langSelect).toHaveValue('fr');
    });
});
