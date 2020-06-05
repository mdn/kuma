//@flow
import * as React from 'react';
import { useContext } from 'react';

import Dropdown from './dropdown.jsx';
import { getLocale, gettext, interpolate } from '../l10n.js';
import UserProvider from '../user-provider.jsx';
import SignInLink from '../signin-link.jsx';

export default function Login(): React.Node {
    const locale = getLocale();
    const userData = useContext(UserProvider.context);

    // if we don't have the user data yet, don't render anything
    if (!userData || typeof window === 'undefined') {
        return null;
    }

    // In order to render links properly, we need to know our own URL.
    // We get this from window.location. This is not available during
    // server side rendering, but this code will never run during
    // server side rendering because we won't have user data then.
    const LOCATION = window.location.pathname;

    if (userData.isAuthenticated && userData.username) {
        // If we have user data and the user is logged in, show their
        // profile pic, defaulting to the dino head if the avatar
        // URL doesn't work.
        let label = (
            <>
                <img
                    src={userData.avatarUrl || '/static/img/avatar.png'}
                    className="avatar"
                    alt={userData.username}
                />
                <span className="username">{userData.username}</span>
            </>
        );
        let viewProfileLink = `/${locale}/profiles/${userData.username}`;
        let contributionsLink = `/${locale}/dashboards/revisions?user=${encodeURIComponent(
            userData.username
        )}`;
        let editProfileLink = `${viewProfileLink}/edit`;

        return (
            <div className="auth-container">
                <Dropdown
                    id="user-avatar-menu"
                    label={label}
                    right={true}
                    hideArrow={true}
                >
                    {!!userData.wikiContributions && (
                        <li>
                            <a
                                href={contributionsLink}
                                title={interpolate(
                                    gettext(
                                        'You have %(count)s Wiki revisions'
                                    ),
                                    {
                                        count:
                                            userData.wikiContributions &&
                                            userData.wikiContributions.toLocaleString(),
                                    }
                                )}
                            >
                                {gettext('Contributions')}
                            </a>
                        </li>
                    )}
                    <li>
                        <a href={viewProfileLink}>{gettext('View profile')}</a>
                    </li>
                    <li>
                        <a href={editProfileLink}>{gettext('Edit profile')}</a>
                    </li>
                    <li>
                        <form action={`/${locale}/users/signout`} method="post">
                            <input name="next" type="hidden" value={LOCATION} />
                            <button className="signout-button" type="submit">
                                {gettext('Sign out')}
                            </button>
                        </form>
                    </li>
                </Dropdown>
            </div>
        );
    } else {
        // Otherwise, show a login prompt
        return <SignInLink className="signin-link" />;
    }
}
