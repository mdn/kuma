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

    // In order to render links properly, we need to know our own URL.
    // We get this from window.location. This is not available during
    // server side rendering, but this code will never run during
    // server side rendering because we won't have user data then.
    const LOCATION = window.location.pathname;

    /**
     * Send a signal to GA when a user clicks on the Sing In
     * lnk in the header.
     * @param {Object} event - The event object that was triggered
     */
    function sendSignInEvent() {
        ga('send', {
            hitType: 'event',
            eventCategory: 'Authentication',
            eventAction: 'Started sign-in',
        });
    }

    /**
     * If you click the "Sign in" link, reach out to the global
     * 'windown.mdn.triggerAuthModal' if it's available.
     *
     * @param {Object} event - The click event
     */
    function triggerAuthModal(event) {
        // If window.mdn.triggerAuthModal is available, use that. But note, the
        // 'event' here is a React synthetic event object, not a regular DOM
        // event. So, we prevent *this* synthetic event and hand over to the
        // global window.mdn.triggerAuthModal() function to take over.
        if (window.mdn && window.mdn.triggerAuthModal) {
            event.preventDefault();
            window.mdn.triggerAuthModal();
        }
    }

    if (userData.isAuthenticated && userData.username) {
        // If we have user data and the user is logged in, show their
        // profile pic, defaulting to the dino head if the avatar
        // URL doesn't work.
        let label = (
            <img
                srcSet={`${userData.avatarUrl || ''} 200w, ${
                    userData.avatarUrl || ''
                } 50w`}
                src={'/static/img/avatar.png'}
                className="avatar"
                alt={userData.username}
            />
        );
        let viewProfileLink = `/${locale}/profiles/${userData.username}`;
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
                href={`/${locale}/users/account/signup-landing?next=${LOCATION}`}
                rel="nofollow"
                className="signin-link"
                onClick={(event) => {
                    // The old GitHub click event (even though it's not GitHub yet).
                    sendSignInEvent();
                    // The action that causes the auth modal to appear.
                    triggerAuthModal(event);
                }}
            >
                {gettext('Sign in')}
            </a>
        );
    }
}
