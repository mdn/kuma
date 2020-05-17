//@flow
import * as React from 'react';

import Dropdown from './dropdown.jsx';
import { gettext, interpolate } from '../l10n.js';

import type { DocumentData } from '../document.jsx';

type Props = {
    document: ?DocumentData,
};

export default function LanguageMenu({ document }: Props): React.Node {
    // If there are no translations available and there is no translateURL,
    // don't display anything.
    if (
        !document ||
        !(document.translations.length > 0 || document.translateURL)
    ) {
        return null;
    }

    // For the menu label, we want to use the name of the document language.
    // We need a special case for English because English documents can
    // appear in pages for other locales, and in that case we need a
    // translation for the word "English". In all other cases, the
    // locale of the page and the locale of the document should match
    // and we can just use the document language string without translation.
    let label =
        document.locale === 'en-US' ? gettext('English') : document.language;
    let chooseLanguageString = interpolate(
        gettext('Current language is %s. Choose your preferred language.'),
        [label]
    );

    return (
        <Dropdown
            id="header-language-menu"
            componentClassName="language-menu"
            label={label}
            right={true}
            ariaOwns="language-menu"
            ariaLabel={chooseLanguageString}
        >
            {document.translations.map((t) => (
                <li key={t.locale} lang={t.locale} role="menuitem">
                    <a href={t.url} title={t.localizedLanguage}>
                        <bdi>{t.language}</bdi>
                    </a>
                </li>
            ))}
            {document.translateURL && (
                <li>
                    <a
                        href={document.translateURL}
                        rel="nofollow"
                        id="translations-add"
                    >
                        {gettext('Add a translation')}
                    </a>
                </li>
            )}
        </Dropdown>
    );
}
