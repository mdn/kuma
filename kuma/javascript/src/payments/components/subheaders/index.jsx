//@flow
import * as React from 'react';

type Props = {
    title: string,
    subtitle?: ?string,
    description?: string,
    children?: React.Node,
    columnWidth?: string,
};

const SubHeader = ({
    title,
    subtitle,
    description,
    columnWidth = 'all', // number of columns, based on grid system defined in _columns.scss
    children,
}: Props): React.Node => (
    <div data-testid="subheader" className="subscriptions subheader-container">
        <div className="column-container">
            <div className={`column-${columnWidth}`}>
                <h1 className="highlight highlight-spanned">
                    <span className="highlight-span">{title}</span>
                </h1>
                {subtitle && <h2>{subtitle}</h2>}
                {description && (
                    <p className="readable-line-length">{description}</p>
                )}
            </div>
            {children}
        </div>
    </div>
);

export default SubHeader;
