// @flow
import * as React from 'react';

import type { DocumentData } from './document.jsx';

type DocumentProps = {
    document: DocumentData
};

export default function Breadcrumbs({ document }: DocumentProps) {
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
