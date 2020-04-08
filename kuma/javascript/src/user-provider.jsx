// @flow
import * as React from 'react';
import { useContext, useEffect, useState } from 'react';

import GAProvider from './ga-provider.jsx';

export type UserData = {
    username: ?string,
    isAuthenticated: boolean,
    isBetaTester: boolean,
    isContributor?: boolean, // This is not implemented on backend yet
    isStaff: boolean,
    isSuperuser: boolean,
    avatarUrl: ?string,
    isSubscriber: boolean,
    subscriberNumber: ?number,
    email: ?string,
    waffle: {
        flags: { [flag_name: string]: boolean },
        switches: { [switch_name: string]: boolean },
        samples: { [sample_name: string]: boolean },
    },
};

const defaultUserData: UserData = {
    username: null,
    isAuthenticated: false,
    isBetaTester: false,
    isStaff: false,
    isSuperuser: false,
    avatarUrl: null,
    isSubscriber: false,
    subscriberNumber: null,
    email: null,
    waffle: {
        flags: {},
        switches: {},
        samples: {},
    },
};

const context = React.createContext<?UserData>(defaultUserData);

export default function UserProvider(props: {
    children: React.Node,
}): React.Node {
    const [userData, setUserData] = useState<?UserData>(null);
    const ga = useContext(GAProvider.context);

    useEffect(() => {
        let dismounted = false;
        fetch('/api/v1/whoami')
            .then((response) => response.json())
            .then((data) => {
                // No point attempting to update state if the component
                // is dismounted.
                if (dismounted) {
                    // bail!
                    return;
                }
                let userData = {
                    username: data.username,
                    isAuthenticated: data.is_authenticated,
                    isBetaTester: data.is_beta_tester,
                    isStaff: data.is_staff,
                    isSuperuser: data.is_super_user,
                    avatarUrl: data.avatar_url,
                    isSubscriber: data.is_subscriber,
                    subscriberNumber: data.subscriber_number,
                    email: data.email,
                    // NOTE: if we ever decide that waffle data should
                    // be re-fetched on client-side navigation, we'll
                    // have to create a separate context for it.
                    waffle: data.waffle,
                };

                // Set the userData as a state variable that we provide
                // to anyone that calls `useContext(UserProvider.context)`
                setUserData(userData);

                // Once the user data has loaded, set some Google
                // Analytics variables and then send the initial
                // pageview event to GA.
                if (userData.isAuthenticated) {
                    ga('set', 'dimension1', 'Yes');
                    if (userData.isBetaTester) {
                        ga('set', 'dimension2', 'Yes');
                    }
                    if (userData.isStaff) {
                        ga('set', 'dimension18', 'Yes');
                    }
                }

                if (userData.waffle.flags.section_edit) {
                    ga('set', 'dimension9', 'Yes');
                }

                // We only fetch user data once, right after the
                // initial page load, so when that user data arrives
                // it is time to send the initial 'pageview' event for
                // the initial load. See router.jsx for code that
                // sends 'pageview' events for client-side navigation.
                ga('send', {
                    hitType: 'pageview',
                    hitCallback: () => {
                        // If the user came to the site by following a
                        // link that has a 'utm' tracker in it, then
                        // after we report that data to google
                        // analytics, we use replaceState to clean up
                        // the location bar
                        if (window.location.search.includes('utm_')) {
                            window.history.replaceState(
                                {},
                                '',
                                window.location.pathname
                            );
                        }
                    },
                });
            });
        return () => {
            dismounted = true;
        };
    }, [ga]); // only fetch on mount, or if `ga` changes

    return (
        <context.Provider value={userData}>{props.children}</context.Provider>
    );
}

UserProvider.context = context;
UserProvider.defaultUserData = defaultUserData;
