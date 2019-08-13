//@flow
import * as React from 'react';
import { useContext } from 'react';

import { css } from '@emotion/core';

import Dropdown from './dropdown.jsx';
import { getLocale, gettext } from '../l10n.js';
import { Row } from '../layout.jsx';
import UserProvider from '../user-provider.jsx';

const styles = {
    container: css({
        gridArea: 'L',
        justifySelf: 'center',
        // Buttons (in the dropdown labels) don't seem to inherit fontsizes
        // so we need to make this explicit.
        button: { fontSize: '1em' }
    }),
    avatar: css({
        width: 40,
        height: 40,
        borderRadius: '50%'
    }),
    signInLink: css({
        display: 'flex',
        alignItems: 'center',
        justifySelf: 'center',
        fontSize: '1em',
        fontWeight: 'bold',
        color: 'black',
        marginLeft: 24,
        textDecoration: 'none',
        ':hover': {
            textDecoration: 'none',
            backgroundColor: '#eee'
        },
        ':focus': {
            // Focus outline extends beyond header in Chrome without this
            outlineOffset: -3
        }
    }),
    signOutButton: css({
        // Signing out is a POST operation so we use a form and button
        // but we want the button to look like a regular link.
        borderWidth: 0,
        padding: 0,
        color: '#3d7e9a'
    }),
    editLink: css({ lineHeight: 1 }),
    editIcon: css({ width: '1.33em' })
};

export default function Login(): React.Node {
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

    if (userData.isAuthenticated && userData.username) {
        // If we have user data and the user is logged in, show their
        // profile pic, defaulting to the dino head if the gravatar
        // URLs don't work.
        let label = (
            <img
                srcSet={`${userData.gravatarUrl.large || ''} 200w, ${userData
                    .gravatarUrl.small || ''} 50w`}
                src={'/static/img/avatar.png'}
                css={styles.avatar}
                alt={userData.username}
            />
        );
        let viewProfileLink = `${WIKI}/${locale}/profiles/${userData.username}`;
        let editProfileLink = `${viewProfileLink}/edit`;

        return (
            <Row css={styles.container}>
                <Dropdown label={label} right={true} hideArrow={true}>
                    <li>
                        <a href={viewProfileLink}>{gettext('View profile')}</a>
                    </li>
                    <li>
                        <a href={editProfileLink}>{gettext('Edit profile')}</a>
                    </li>
                    <li>
                        <form action={`/${locale}/users/signout`} method="post">
                            <input name="next" type="hidden" value={LOCATION} />
                            <button css={styles.signOutButton} type="submit">
                                {gettext('Sign out')}
                            </button>
                        </form>
                    </li>
                </Dropdown>
            </Row>
        );
    } else {
        // Otherwise, show a login prompt
        return (
            <a
                href={`/users/github/login/?next=${LOCATION}`}
                data-service="GitHub"
                rel="nofollow"
                css={styles.signInLink}
            >
                {gettext('Sign in')}
            </a>
        );
    }
}
