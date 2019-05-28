//@flow
import * as React from 'react';
import { useContext } from 'react';

import { css } from '@emotion/core';

import DocumentProvider from '../document-provider.jsx';
import Dropdown from './dropdown.jsx';
import { getLocale, gettext } from '../l10n.js';
import { Row } from '../layout.jsx';
import UserProvider from '../user-provider.jsx';

const styles = {
    container: css({
        // Buttons (in the dropdown labels) don't seem to inherit fontsizes
        // so we need to make this explicit.
        button: { fontSize: '1em' },
        marginLeft: 24
    }),
    avatar: css({
        width: 40,
        height: 40,
        borderRadius: '50%'
    }),
    signInLink: css({
        display: 'flex',
        alignItems: 'center',
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
        color: '#3d7e9a',
        fontSize: '1em',
        fontWeight: 'normal',
        ':hover': { textDecoration: 'underline' }
    }),
    editLink: css({ lineHeight: 1 }),
    editIcon: css({ width: '1.33em' })
};

export default function Login(): React.Node {
    const locale = getLocale();
    const documentData = useContext(DocumentProvider.context);
    if (!documentData) {
        return null;
    }
    const { absoluteURL, editURL } = documentData;
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
        // profile pic, defaulting to the dino head if the gravatar
        // URLs don't work.
        let label = (
            <img
                srcSet={`${userData.gravatarUrl.large || ''} 200w ${userData
                    .gravatarUrl.small || ''} 50w`}
                src={'/static/img/avatar.png'}
                css={styles.avatar}
                alt={userData.username}
            />
        );
        let viewProfileLink = `${WIKI_SITE_URL}/${locale}/profiles/${
            userData.username
        }`;
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
                        <form
                            action={`${WIKI_SITE_URL}/${locale}/users/signout`}
                            method="post"
                        >
                            <input name="next" type="hidden" value={PATHNAME} />
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
                href={`${WIKI_SITE_URL}/users/github/login/?next=${PATHNAME}`}
                data-service="GitHub"
                rel="nofollow"
                css={styles.signInLink}
            >
                {gettext('Sign in')}
            </a>
        );
    }
}
