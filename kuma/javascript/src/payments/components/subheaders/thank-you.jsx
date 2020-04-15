// @flow
import * as React from 'react';
import SubHeader from './index.jsx';
import { gettext, interpolate } from '../../../l10n.js';

type Props = {
    num?: ?number,
};

export const title = gettext('Thank you for becoming a monthly supporter!');
export const subtitle = gettext('You are MDN member number %(num)s');

const ThankYouSubheader = ({ num }: Props): React.Node => {
    const subtitleInterpolated = num
        ? interpolate(subtitle, {
              num: num.toLocaleString(),
          })
        : null;
    return <SubHeader title={title} subtitle={subtitleInterpolated} />;
};

export default ThankYouSubheader;
