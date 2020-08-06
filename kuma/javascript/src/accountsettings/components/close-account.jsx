// @flow
import * as React from 'react';

import { type UserData } from '../../user-provider.jsx';
import { gettext } from '../../l10n.js';

type Props = {
    locale: string,
    userData: UserData,
};

const CloseAccount = ({ locale, userData }: Props) => {
    const { username }: any = userData;

    return (
        <section
            className="subscription account-girdle"
            aria-labelledby="close-account-heading"
        >
            <h2 id="close-account-heading">{gettext('Close Account')}</h2>

            <div className="lead-in">
                <p>{gettext('Delete your account and account data.')}</p>
                <a
                    href={`/${locale}/profiles/${username}/delete`}
                    className="cta negative"
                >
                    {gettext('Close account')}
                </a>
            </div>
        </section>
    );
};

export default CloseAccount;
