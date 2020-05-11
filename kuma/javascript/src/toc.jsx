// @flow
import * as React from 'react';
import { useContext, useState } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';

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
     * Returns the related topics list item to be appended
     * to the end of the TOC items list.
     */
    function relatedTopicsListitem() {
        return (
            <li className="toc-related-topics">
                <a href="#sidebar-quicklinks">{gettext('Related topics')}</a>
            </li>
        );
    }

    /**
     * Returns the HTML for the table of contents with the
     * related topics list item appended to the end of the
     * original list.
     *
     * NOTE: The reason this is needed is because the initial
     * list of table of content entries is retrieved from the
     * document API and provided as raw HTML. The additional
     * entry is not provided by the API and thus, we need to
     * manually append it here.
     *
     * At the time of writing this is the only way to have both
     * raw HTML and React elements as siblings
     */
    function getTOCHTML() {
        return html + renderToStaticMarkup(relatedTopicsListitem());
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
                        __html: getTOCHTML(),
                    }}
                />
            </section>
        </aside>
    );
}
