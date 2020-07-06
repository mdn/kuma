// @flow
import * as React from 'react';
import { useState } from 'react';

import { gettext } from '../../l10n.js';

import CloseAccountForm from './close-account-form.jsx';

const CloseAccount = () => {
    const [showForm, setShowForm] = useState<boolean>(false);

    return (
        <section
            className="subscription account-girdle"
            aria-labelledby="close-account-heading"
        >
            <h2 id="close-account-heading">{gettext('Close Account')}</h2>

            <div className="lead-in">
                <p>{gettext('Delete your account and account data.')}</p>
                <button
                    className="cta negative"
                    type="button"
                    onClick={() => {
                        setShowForm(true);
                    }}
                >
                    {gettext('Close account')}
                </button>
            </div>

            {showForm && (
                <CloseAccountForm onCancel={() => setShowForm(false)} />
            )}
        </section>
    );
};

export default CloseAccount;
