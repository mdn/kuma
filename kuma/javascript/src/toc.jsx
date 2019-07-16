// @flow
import * as React from 'react';
import { gettext } from './l10n.js';

type TOCProps = {
    html: string
};

export default function TOC({ html }: TOCProps) {
    return (
        <aside className="document-toc-container">
            <section className="document-toc">
                <header>
                    <h2> {gettext('On this Page')}</h2>
                </header>
                <ul
                    dangerouslySetInnerHTML={{
                        __html: html
                    }}
                />
            </section>
        </aside>
    );
}
