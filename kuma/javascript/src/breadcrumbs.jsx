// @flow
import * as React from 'react';
import { useContext } from 'react';

import GAProvider from './ga-provider.jsx';

import type { DocumentData } from './document.jsx';

type DocumentProps = {
    document: DocumentData,
};

export default function Breadcrumbs({ document }: DocumentProps) {
    const ga = useContext(GAProvider.context);

    /**
     * Send a signal to GA when there is an interaction on one
     * of the breadcrumb menu links.
     * @param {Object} event - The event object that was triggered
     */
    function sendBreadcrumbItemClick(event) {
        const label = event.target.href;

        ga('send', {
            hitType: 'event',
            eventCategory: 'Wiki',
            eventAction: 'Crumbs',
            eventLabel: label,
        });
    }

    return (
        <nav className="breadcrumbs" role="navigation">
            <ol
                typeof="BreadcrumbList"
                vocab="https://schema.org/"
                aria-label="breadcrumbs"
            >
                {document.parents.map((p, i) => (
                    <li
                        key={p.url}
                        property="itemListElement"
                        typeof="ListItem"
                    >
                        <a
                            href={p.url}
                            className="breadcrumb-chevron"
                            property="item"
                            typeof="WebPage"
                            onClick={sendBreadcrumbItemClick}
                            onContextMenu={sendBreadcrumbItemClick}
                        >
                            <span property="name">{p.title}</span>
                        </a>
                        <meta property="position" content={i + 1} />
                    </li>
                ))}
                <li property="itemListElement" typeof="ListItem">
                    <a
                        href={document.absoluteURL}
                        className="crumb-current-page"
                        property="item"
                        typeof="WebPage"
                        onClick={sendBreadcrumbItemClick}
                        onContextMenu={sendBreadcrumbItemClick}
                    >
                        <span property="name" aria-current="page">
                            {document.title}
                        </span>
                    </a>
                    <meta
                        property="position"
                        content={document.parents.length + 1}
                    />
                </li>
            </ol>
        </nav>
    );
}
