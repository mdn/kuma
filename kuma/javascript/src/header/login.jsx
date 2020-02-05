//@flow
import * as React from 'react';
import { useContext } from 'react';

import Dropdown from './dropdown.jsx';
import { getLocale, gettext } from '../l10n.js';
import UserProvider from '../user-provider.jsx';
import GAProvider from '../ga-provider.jsx';

export default function Login(): React.Node {
    const ga = useContext(GAProvider.context);
    const locale = getLocale();
    const userData = useContext(UserProvider.context);

    // if we don't have the user data yet, don't render anything
    if (!userData || typeof window === 'undefined') {
        return null;
    }

    // In order to render links properly, we need to know our own
    // URL and the URL of the editable wiki site. We get these from
    // window.location and from window.mdn. Neither of those are
    // available during server side rendering, but this code will
    // never run during server side rendering because we won't have
    // user data then.
    const LOCATION = window.location.pathname;
    const WIKI = window.mdn ? window.mdn.wikiSiteUrl : '';

    /**
     * Send a signal to GA when a user clicks on the Sing In
     * lnk in the header.
     * @param {Object} event - The event object that was triggered
     */
    function sendSignInEvent(event) {
        const service = event.target.dataset.service;

        ga('send', {
            hitType: 'event',
            eventCategory: 'Authentication',
            eventAction: 'Started sign-in',
            eventLabel: service
        });
    }

    if (userData.isAuthenticated && userData.username) {
        // If we have user data and the user is logged in, show their
        // profile pic, defaulting to the dino head if the avatar
        // URL doesn't work.
        let label = (
            <img
                srcSet={`${userData.avatarUrl ||
                    ''} 200w, ${userData.avatarUrl || ''} 50w`}
                src={'/static/img/avatar.png'}
                className="avatar"
                alt={userData.username}
            />
        );
        let viewProfileLink = `${WIKI}/${locale}/profiles/${userData.username}`;
        let editProfileLink = `${viewProfileLink}/edit`;

        return (
            <div className="auth-container">
                <Dropdown
                    id="user-avatar-menu"
                    label={label}
                    right={true}
                    hideArrow={true}
                >
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
        return (
            <a
                href={
                    (window && window.mdn && window.mdn.multiAuthEnabled
                        ? `/${locale}/users/account/signup-landing`
                        : '/users/github/login') + `?next=${LOCATION}`
                }
                data-service="GitHub"
                rel="nofollow"
                className="signin-link"
                onClick={sendSignInEvent}
            >
                {gettext('Sign in')}
            </a>
        );
    }
}
