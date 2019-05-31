//@flow
import * as React from 'react';

import Dropdown from './dropdown.jsx';
import { gettext } from '../l10n.js';

import type { DocumentData } from '../document.jsx';

type Props = {
    document: ?DocumentData
};

export default function LanguageMenu({ document }: Props): React.Node {
    // If there aren't any translations available, don't display anyhing
    if (!document || document.translations.length === 0) {
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

    return (
        <Dropdown label={label} right={true}>
            {document.translations.map(t => (
                <li key={t.locale} lang={t.locale}>
                    <a href={t.url} title={t.localizedLanguage}>
                        <bdi>{t.language}</bdi>
                    </a>
                </li>
            ))}
        </Dropdown>
    );
}
