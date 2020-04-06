// @flow
import * as React from 'react';
import { gettext, interpolate } from '../l10n.js';
import SubHeader from './subheader.jsx';

type Props = {
    subscriberNumber: ?number,
};

export const title = 'Thank you for becoming a monthly supporter!';
export const subtitle = (num: ?number): ?string => {
    if (num) {
        return interpolate(gettext('You are MDN member number: %s'), [
            num.toLocaleString(),
        ]);
    }
    return null;
};

const ThankYouSubheader = ({ subscriberNumber }: Props): React.Node => (
    <SubHeader title={title} subtitle={subtitle(subscriberNumber)} />
);
export default ThankYouSubheader;
