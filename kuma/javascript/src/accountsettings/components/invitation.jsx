// @flow
import * as React from 'react';

import { gettext, Interpolated } from '../../l10n.js';

type Props = {
    locale: string,
};

const Invitation = ({ locale }: Props) => {
    return (
        <div className="active-subscriptions">
            <p>
                <Interpolated
                    id={gettext(
                        'You have no active subscription. Why not <signupLink />?'
                    )}
                    signupLink={
                        <a href={`/${locale}/payments/`}>
                            {gettext('set one up')}
                        </a>
                    }
                />
            </p>
        </div>
    );
};

export default Invitation;
