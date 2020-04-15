// @flow
import * as React from 'react';

import { gettext, Interpolated } from '../l10n.js';

type Props = {
    isSubscriber: ?boolean,
};

const nonSubscriberDiscountCopy = gettext(
    'Get discounts on sweet loot from the <merchStoreLink />.'
);
export const nonSubscriberInvitationCopy = gettext(
    'Get invited to attend special events and conferences.'
);
const subscriberDiscountCopy = gettext(
    'Get 20% of the <merchStoreLink /> with discount code MDNMEMBER20.'
);
export const subscriberInvitationCopy = gettext(
    'Check back for invitations to attend special events and conferences.'
);

const Incentives = ({ isSubscriber = false }: Props) => {
    const merchStoreURL =
        'https://shop.spreadshirt.com/mozilla-developer-network/';
    return (
        <div className="subscriptions-incentive">
            <h3>{gettext('Enjoy exclusive member perks')}</h3>
            <ul className="perks">
                <li className="discounts">
                    <h4>{gettext('Discounts on swag')}</h4>
                    <p>
                        <Interpolated
                            id={
                                isSubscriber
                                    ? subscriberDiscountCopy
                                    : nonSubscriberDiscountCopy
                            }
                            merchStoreLink={
                                <a
                                    href={merchStoreURL}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    {gettext('MDN Merch store')}
                                </a>
                            }
                        />
                    </p>
                </li>
                <li className="invitations">
                    <h4>{gettext('Invitations to events')}</h4>
                    <p>
                        {!isSubscriber
                            ? nonSubscriberInvitationCopy
                            : subscriberInvitationCopy}
                    </p>
                </li>
            </ul>
        </div>
    );
};

export default Incentives;
