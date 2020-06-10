// @flow
import * as React from 'react';

type Props = {
    pageTitle: string,
    pageSubtitle: string,
    userData: Object,
};

const Titlebar = ({ pageTitle, pageSubtitle, userData }: Props) => {
    const avatarUrl = userData && userData.avatarUrl;

    return (
        <header className="account-girdle accountsettings-titlebar">
            <img src={avatarUrl} className="avatar" width="90" alt="" />
            <div className="txt-container">
                <h2>{pageTitle}</h2>
                <p className="foonote">{pageSubtitle}</p>
            </div>
        </header>
    );
};

export default Titlebar;
