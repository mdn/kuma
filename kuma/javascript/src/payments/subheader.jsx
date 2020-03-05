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

const SubHeader = ({
    title,
    subtitle,
    description,
    columnWidth = 'all', // number of columns, based on grid system defined in _columns.scss
    children
}: Props): React.Node => (
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

export default SubHeader;
