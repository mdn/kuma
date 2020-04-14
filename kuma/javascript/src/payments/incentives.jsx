// @flow
import * as React from 'react';

import { gettext, Interpolated } from '../l10n.js';

type Props = {
    isSubscriber: Boolean,
    locale: string,
};

const nonSubscriberDiscountCopy = gettext(
    'Get discounts on sweet loot from the <merchStoreLink />'
);
export const nonSubscriberInvitationCopy = gettext(
    'Get invited to attend special events and conferences.'
);
const subscriberDiscountCopy = gettext(
    'Get 30% of the <merchStoreLink /> with discount code MDNMEMBER30'
);
export const subscriberInvitationCopy = gettext(
    'Check back for invitations to attend special events and conferences.'
);

const Incentives = ({ isSubscriber, locale }: Props) => {
    return (
        <div className="subscriptions-incentive">
            <h3>{gettext('Enjoy exclusive member perks')}</h3>
            <ul className="perks">
                <li className="discounts">
                    <h4>{gettext('Discounts on swag')}</h4>
                    <p>
                        {!isSubscriber && (
                            <Interpolated
                                id={nonSubscriberDiscountCopy}
                                merchStoreLink={
                                    <a href={`/${locale}/payments/terms/`}>
                                        {gettext('MDN Merch store')}
                                    </a>
                                }
                            />
                        )}

                        {isSubscriber && (
                            <Interpolated
                                id={subscriberDiscountCopy}
                                merchStoreLink={
                                    <a href={`/${locale}/payments/terms/`}>
                                        {gettext('MDN Merch store')}
                                    </a>
                                }
                            />
                        )}
                    </p>
                </li>
                <li className="invitations">
                    <h4>{gettext('Invitations to events')}</h4>
                    <p>
                        {!isSubscriber && nonSubscriberInvitationCopy}

                        {isSubscriber && subscriberInvitationCopy}
                    </p>
                </li>
            </ul>
        </div>
    );
};

export default Incentives;
