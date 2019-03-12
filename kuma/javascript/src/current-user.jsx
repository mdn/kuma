// @flow
import * as React from 'react';
import { useState, useEffect } from 'react';

export type UserData = {
    username: ?string,
    isAuthenticated: boolean,
    isBetaTester: boolean,
    isStaff: boolean,
    isSuperuser: boolean,
    timezone: ?string,
    gravatarUrl: {
        small: ?string,
        large: ?string
    }
};

const defaultUserData: UserData = {
    username: null,
    isAuthenticated: false,
    isBetaTester: false,
    isStaff: false,
    isSuperuser: false,
    timezone: null,
    gravatarUrl: { small: null, large: null }
};

const context = React.createContext<?UserData>(defaultUserData);

function Provider(props: { children: React.Node }): React.Node {
    const [userData, setUserData] = useState<?UserData>(null);
    useEffect(() => {
        fetch('/api/v1/whoami')
            .then(response => response.json())
            .then(data => {
                setUserData({
                    username: data.username,
                    isAuthenticated: data.is_authenticated,
                    isBetaTester: data.is_beta_tester,
                    isStaff: data.is_staff,
                    isSuperuser: data.is_super_user,
                    timezone: data.timezone,
                    gravatarUrl: data.gravatar_url
                });
            });
    }, []); // empty array means we only fetch on mount, not on every render

    return (
        <context.Provider value={userData}>{props.children}</context.Provider>
    );
}

export default { context, defaultUserData, Provider };
