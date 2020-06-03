// @flow
import * as React from 'react';

import { gettext } from '../../l10n.js';
import LanguageSelect from './language-select.jsx';

type Props = {
    locale: string,
    userData: Object,
    sortedLanguages: Object,
};

const UserDetails = ({ locale, userData, sortedLanguages }: Props) => {
    const { email, username } = userData;

    return (
        <form
            name="user-details"
            method="post"
            action=""
            className="account-girdle user-details"
            data-testid="user-details-form"
        >
            <fieldset>
                <ul className="form-fields-list">
                    <li>
                        <div className="label">{gettext('Email')}</div>
                        {email}
                        <p>
                            <a href={`/${locale}/users/account/email`}>
                                {gettext('Manage email addresses')}
                            </a>
                        </p>
                    </li>
                    <li>
                        <label>
                            <input
                                type="checkbox"
                                id="newsletter-subscriber"
                                name="user-is_newsletter_subscribed"
                            />
                            {gettext(
                                'Get exclusive content, offers and invitations to your inbox'
                            )}
                        </label>
                    </li>
                    <li>
                        <label htmlFor="username">{gettext('Username')}</label>
                        <input
                            type="text"
                            id="username"
                            name="user-username"
                            defaultValue={username}
                            maxLength="30"
                        />
                    </li>
                    <li>
                        <label htmlFor="user-fullname">{gettext('Name')}</label>
                        <input
                            type="text"
                            id="user-fullname"
                            name="user-fullname"
                            maxLength="255"
                        />
                    </li>
                    <li>
                        <LanguageSelect
                            label={gettext('Language')}
                            name="user-locale"
                            sortedLanguages={sortedLanguages}
                        />
                    </li>
                    <li>
                        <button type="submit" className="cta primary">
                            {gettext('Save')}
                        </button>
                    </li>
                </ul>
            </fieldset>
        </form>
    );
};

export default UserDetails;
