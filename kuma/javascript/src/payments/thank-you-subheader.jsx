// @flow
import * as React from 'react';
import { gettext, interpolate } from '../l10n.js';
import SubHeader from './subheader.jsx';

type Props = {
    subscriberNumber: ?number,
};

export const title = 'Thank you for becoming a monthly supporter!';
export const subtitle = 'You are MDN member number:';
export const getSubtitle = (num: ?number): ?string => {
    if (num) {
        return interpolate(gettext('%(subtitle)s %(num)s'), {
            subtitle,
            num: num.toLocaleString(),
        });
    }
    return null;
};

const ThankYouSubheader = ({ subscriberNumber }: Props): React.Node => (
    <SubHeader title={title} subtitle={getSubtitle(subscriberNumber)} />
);

export default ThankYouSubheader;
