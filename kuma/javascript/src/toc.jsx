// @flow
import * as React from 'react';
import { useContext, useEffect, useRef } from 'react';

import GAProvider from './ga-provider.jsx';
import { gettext } from './l10n.js';

type Props = {
    html: string,
};

export default function TOC({ html }: Props) {
    const ga = useContext(GAProvider.context);
    const tocRef = useRef(null);

    /**
     * Send a signal to GA when the user clicks on one of links
     * in the table of contents
     * @param {Object} event - The event object that was triggered
     */
    function sendTOCClicks(event: MouseEvent) {
        if (event.target instanceof HTMLAnchorElement) {
            const action = event.target.textContent;
            const label = new URL(event.target.href).hash;

            ga('send', {
                hitType: 'event',
                eventCategory: 'MozMenu',
                eventAction: action,
                eventLabel: label,
            });
        }
    }

    useEffect(() => {
        const documentToc = tocRef.current;

        if (documentToc) {
            documentToc.addEventListener('click', sendTOCClicks);
        }

        return () => {
            if (documentToc) {
                documentToc.removeEventListener('click', sendTOCClicks);
            }
        };
    });

    return (
        <aside className="document-toc-container">
            <section className="document-toc" ref={tocRef}>
                <header>
                    <h2>{gettext('On this Page')}</h2>
                </header>
                <ul
                    dangerouslySetInnerHTML={{
                        __html: html,
                    }}
                />
            </section>
        </aside>
    );
}
