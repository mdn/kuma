// @flow
import * as React from 'react';
import SubHeader from './subheader.jsx';
import { strings, getMemberNumberString } from './strings.js';

type Props = {
    subscriberNumber?: ?number,
    isSubscriber?: ?boolean,
};

const ThankYouSubheader = ({
    subscriberNumber,
    isSubscriber,
}: Props): React.Node => (
    <SubHeader
        title={strings.thankYou}
        subtitle={getMemberNumberString(subscriberNumber, isSubscriber)}
    />
);

export default ThankYouSubheader;
