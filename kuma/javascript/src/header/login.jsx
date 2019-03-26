//@flow
import * as React from 'react';
import { useContext } from 'react';

import { css } from '@emotion/core';

import CurrentUser from '../current-user.jsx';
import DocumentProvider from '../document-provider.jsx';
import Dropdown from './dropdown.jsx';
import EditIcon from '../icons/pencil.svg';
import gettext from '../gettext.js';
import GithubLogo from '../icons/github.svg';
import { Strut } from '../layout.jsx';

const strings = {
    signIn: gettext('Sign in'),
    viewProfile: gettext('View profile'),
    editProfile: gettext('Edit profile'),
    signOut: gettext('Sign out')
};

const styles = {
    avatar: css({
        width: 48,
        height: 48,
        borderRadius: '50%'
    }),
    signInLink: css({
        display: 'flex',
        alignItems: 'center',
        fontSize: 18,
        fontWeight: 'bold',
        color: 'black',
        textDecoration: 'none',
        lineHeight: '48px',
        padding: '0 8px',
        ':hover': {
            textDecoration: 'none',
            backgroundColor: '#eee'
        },
        ':focus': {
            // Focus outline extends beyond header in Chrome without this
            outlineOffset: -3
        }
    }),
    icon: css({ marginLeft: 5 }),
    signOutButton: css({
        // Signing out is a POST operation so we use a form and button
        // but we want the button to look like a regular link.
        borderWidth: 0,
        padding: 0,
        color: '#3d7e9a',
        fontWeight: 'normal',
        ':hover': { textDecoration: 'underline' }
    }),
    editLink: css({ lineHeight: 1 })
};

export default function Login(): React.Node {
    const documentData = useContext(DocumentProvider.context);
    if (!documentData) {
        return null;
    }
    const { editURL, localeFromURL } = documentData;
    const userData = useContext(CurrentUser.context);
    const PATHNAME = window && window.location ? window.location.pathname : '/';
    const WIKI_SITE_URL = window && window.mdn ? window.mdn.wikiSiteUrl : '';

    // if we don't have the user data yet, don't render anything
    if (!userData) {
        return null;
    }

    if (userData.isAuthenticated && userData.username) {
        // If we have user data and the user is logged in, show their
        // profile pic.
        let label = (
            <img
                src={userData.gravatarUrl.small}
                css={styles.avatar}
                alt={userData.username}
            />
        );
        return (
            <>
                <Dropdown label={label} right={true}>
                    <li>
                        <a
                            href={`${WIKI_SITE_URL}/${localeFromURL}/profiles/${
                                userData.username
                            }`}
                        >
                            {strings.viewProfile}
                        </a>
                    </li>
                    <li>
                        <a
                            href={`${WIKI_SITE_URL}/${localeFromURL}/profiles/${
                                userData.username
                            }/edit`}
                        >
                            {strings.editProfile}
                        </a>
                    </li>
                    <li>
                        <form
                            action={`${WIKI_SITE_URL}/${localeFromURL}/users/signout`}
                            method="post"
                        >
                            <input name="next" type="hidden" value={PATHNAME} />
                            <button css={styles.signOutButton} type="submit">
                                {strings.signOut}
                            </button>
                        </form>
                    </li>
                </Dropdown>
                <Strut width={8} />
                <a css={styles.editLink} href={editURL} title="Edit this page">
                    <EditIcon alt="Edit this page" />
                </a>
            </>
        );
    } else {
        // Otherwise, show a login prompt
        return (
            <a
                href={`${WIKI_SITE_URL}/users/github/login/?next=${PATHNAME}`}
                data-service="GitHub"
                rel="nofollow"
                css={styles.signInLink}
            >
                {strings.signIn} <GithubLogo css={styles.icon} />
            </a>
        );
    }
}
