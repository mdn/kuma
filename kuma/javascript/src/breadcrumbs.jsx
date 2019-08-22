// @flow
import * as React from 'react';

import type { DocumentData } from './document.jsx';

type DocumentProps = {
    document: DocumentData
};

export default function Breadcrumbs({ document }: DocumentProps) {
    return (
        <nav className="breadcrumbs" role="navigation">
            <ol>
                {document.parents.map(p => (
                    <li key={p.url}>
                        <a href={p.url} className="breadcrumb-chevron">
                            {p.title}
                        </a>
                    </li>
                ))}
                <li>{document.title}</li>
            </ol>
        </nav>
    );
}
