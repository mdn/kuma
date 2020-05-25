// @flow
import * as React from 'react';

type Props = {
    locale: string,
    pageTitle: string,
    userData: Object,
};

const Titlebar = ({ locale, pageTitle, userData }: Props) => {
    const avatarUrl = userData && userData.avatarUrl;
    const username = userData && userData.username;

    return (
        <header className="account-titlebar">
            <img src={avatarUrl} className="avatar" width="90" alt="" />
            <div className="txt-container">
                <h2>
                    <a href={`/${locale}/accounts`}>{username}</a>
                    {` / ${pageTitle}`}
                </h2>
                <p className="foonote">Update your avatar from</p>
            </div>
        </header>
    );
};

export default Titlebar;
