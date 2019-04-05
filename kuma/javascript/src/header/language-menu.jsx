//@flow
import * as React from 'react';
import { useContext } from 'react';
import { css } from '@emotion/core';

import DocumentProvider from '../document-provider.jsx';
import Dropdown from './dropdown.jsx';
import LanguageIcon from '../icons/language.svg';

const styles = {
    icon: css({
        height: '1.5em'
    })
};

export default function LanguageMenu(): React.Node {
    const documentData = useContext(DocumentProvider.context);

    return (
        documentData && (
            <Dropdown label={<LanguageIcon css={styles.icon} />}>
                {documentData.translations.map(t => (
                    <li key={t.locale} lang={t.locale}>
                        <a href={t.url} title={t.localizedLanguage}>
                            <bdi>{t.language}</bdi>
                        </a>
                    </li>
                ))}
            </Dropdown>
        )
    );
}
