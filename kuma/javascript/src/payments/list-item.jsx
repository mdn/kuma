//@flow
import * as React from 'react';

import { gettext } from '../l10n.js';

type ListItemProps = {
    title: string,
    number: string,
    children: React.Node
};

const ListItem = ({ title, number, children }: ListItemProps) => (
    <li className="faq">
        <h3>{gettext(title)}</h3>
        <span className="faq-number">{number}</span>
        {children}
    </li>
);

export default ListItem;
