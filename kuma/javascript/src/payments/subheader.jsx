//@flow
import * as React from 'react';

import { gettext } from '../l10n.js';

type Props = {
    title: string,
    subtitle?: string,
    description?: string,
    children?: React.Node,
    columnWidth?: string
};

export default function SubHeader({
    title,
    subtitle,
    description,
    columnWidth = 'all',
    children
}: Props): React.Node {
    return (
        <div className="contribution-page-header">
            <div className="column-container">
                <div className={`column-${columnWidth}`}>
                    <h1 className="highlight highlight-spanned">
                        <span className="highlight-span">{gettext(title)}</span>
                    </h1>
                    {subtitle && <h2>{gettext(subtitle)}</h2>}
                    {description && <p>{gettext(description)}</p>}
                </div>
                {children && <>{children}</>}
            </div>
        </div>
    );
}
