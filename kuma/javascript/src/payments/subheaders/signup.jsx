// @flow
import * as React from 'react';
import { gettext, interpolate } from '../../l10n.js';
import SubHeader from './index.jsx';
import SubscriptionForm from '../subscription-form.jsx';

type Props = {
    num: ?number,
    showSubscriptionForm: ?boolean,
};

export const title = gettext('Become a monthly supporter');
export const subtitle = gettext('You will be MDN member number: %(num)s');
export const description = gettext(
    'Support MDN with a %(amount)s monthly subscription and get back more of the knowledge and tools you rely on for when your work has to work.'
);

const SignupSubheader = ({ num, showSubscriptionForm }: Props): React.Node => {
    const subtitleInterpolate = interpolate(gettext(subtitle), {
        num: num && num.toLocaleString(),
    });
    const descriptionInterpolate = interpolate(gettext(description), {
        // Hard-coded until this issue is addressed: https://github.com/mdn/kuma/issues/6654
        amount: '$5',
    });

    return (
        <SubHeader
            title={title}
            subtitle={subtitleInterpolate}
            description={descriptionInterpolate}
            classNames={showSubscriptionForm ? 'has-form' : ''}
        >
            {showSubscriptionForm && <SubscriptionForm />}
        </SubHeader>
    );
};

export default SignupSubheader;
