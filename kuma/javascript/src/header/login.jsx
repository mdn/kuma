//@flow
import * as React from 'react';
import { useContext } from 'react';

import { css } from '@emotion/core';

import DocumentProvider from '../document-provider.jsx';
import Dropdown from './dropdown.jsx';
import EditIcon from '../icons/pencil.svg';
import gettext from '../gettext.js';
import GithubLogo from '../icons/github.svg';
import { Row, Strut } from '../layout.jsx';
import UserProvider from '../user-provider.jsx';

const strings = {
    signIn: gettext('Sign in'),
    viewProfile: gettext('View profile'),
    editProfile: gettext('Edit profile'),
    signOut: gettext('Sign out')
};

const styles = {
    container: css({
        // Buttons (in the dropdown labels) don't seem to inherit fontsizes
        // so we need to make this explicit.
        button: { fontSize: '1em' }
    }),
    avatar: css({
        width: '4em',
        borderRadius: '50%'
    }),
    signInLink: css({
        display: 'flex',
        alignItems: 'center',
        fontSize: '1.2em',
        fontWeight: 'bold',
        color: 'black',
        textDecoration: 'none',
        lineHeight: '3.2em',
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
    icon: css({ marginLeft: 3, width: '1.5em' }),
    signOutButton: css({
        // Signing out is a POST operation so we use a form and button
        // but we want the button to look like a regular link.
        borderWidth: 0,
        padding: 0,
        color: '#3d7e9a',
        fontSize: '1em',
        fontWeight: 'normal',
        ':hover': { textDecoration: 'underline' }
    }),
    editLink: css({ lineHeight: 1 }),
    editIcon: css({ width: '1.33em' })
};

export default function Login(): React.Node {
    const documentData = useContext(DocumentProvider.context);
    if (!documentData) {
        return null;
    }
    const { absoluteURL, editURL, requestLocale } = documentData;
    const userData = useContext(UserProvider.context);

    const PATHNAME = absoluteURL;

    // This is available as window.mdn.wikiSiteUrl. But we can't access
    // that during server-side rendering, so we either need to add that mdn
    // data to the document data, or we need to derive it from existing
    // document data somehow
    // TODO: pass this URL in some more reasonable way
    const WIKI_SITE_URL = editURL.substring(0, editURL.indexOf(absoluteURL));

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
            <Row css={styles.container}>
                <Dropdown label={label} right={true}>
                    <li>
                        <a
                            href={`${WIKI_SITE_URL}/${requestLocale}/profiles/${
                                userData.username
                            }`}
                        >
                            {strings.viewProfile}
                        </a>
                    </li>
                    <li>
                        <a
                            href={`${WIKI_SITE_URL}/${requestLocale}/profiles/${
                                userData.username
                            }/edit`}
                        >
                            {strings.editProfile}
                        </a>
                    </li>
                    <li>
                        <form
                            action={`${WIKI_SITE_URL}/${requestLocale}/users/signout`}
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
                    <EditIcon css={styles.editIcon} alt="Edit this page" />
                </a>
            </Row>
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
