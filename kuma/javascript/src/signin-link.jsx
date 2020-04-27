//@flow
import * as React from 'react';
import { useContext } from 'react';

import { getLocale, gettext } from './l10n.js';
import GAProvider from './ga-provider.jsx';

type Props = {
    className?: string,
    text?: string,
};

export default function SignInLink({
    className,
    text = gettext('Sign in'),
}: Props): React.Node {
    const ga = useContext(GAProvider.context);
    const locale = getLocale();

    if (typeof window === 'undefined') {
        return null;
    }

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

    return (
        <a
            href={`/${locale}/users/account/signup-landing?next=${LOCATION}`}
            rel="nofollow"
            className={className ? className : ''}
            onClick={(event) => {
                // The old GitHub click event (even though it's not GitHub yet).
                sendSignInEvent();
                // The action that causes the auth modal to appear.
                triggerAuthModal(event);
            }}
        >
            {gettext(text)}
        </a>
    );
}
