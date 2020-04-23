// @flow
import * as React from 'react';
import { useContext, useState } from 'react';

import GAProvider from './ga-provider.jsx';
import { gettext } from './l10n.js';

import Caret from './icons/caret-down.svg';

type Props = {
    html: string,
};

export default function TOC({ html }: Props) {
    const ga = useContext(GAProvider.context);
    const [showTOC, setShowTOC] = useState(false);

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

    /**
     * Show or hide the table of contents on
     * mobile devices
     */
    function toggleTOC() {
        setShowTOC(!showTOC);
    }

    return (
        <aside className="document-toc-container">
            {/* eslint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions */}
            <section className="document-toc" onClick={sendTOCClicks}>
                <header>
                    <h2>{gettext('On this Page')}</h2>
                    <button
                        type="button"
                        className="toc-trigger-mobile"
                        onClick={toggleTOC}
                    >
                        {gettext('Jump to section')}
                        <Caret />
                    </button>
                </header>
                <ul
                    className={showTOC ? 'show-toc' : undefined}
                    dangerouslySetInnerHTML={{
                        __html: html,
                    }}
                />
            </section>
        </aside>
    );
}
