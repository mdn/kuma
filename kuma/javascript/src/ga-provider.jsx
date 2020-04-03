// @flow
import * as React from 'react';
import { useContext, useEffect, useState } from 'react';

export type GAFunction = (...any) => void;

function ga(...args) {
    if (typeof window === 'object' && typeof window.ga === 'function') {
        window.ga(...args);
    }
}

const context = React.createContext<GAFunction>(ga);

/**
 * If we're running in the browser (not being server-side rendered)
 * and if the HTML document includes the Google Analytics snippet that
 * defines the ga() function, then this provider component makes that
 * ga() function available to any component via:
 *
 *    let ga = useContext(GAProvider.context)
 *
 * If we're not in a browser or if google analytics is not enabled,
 * then we provide a dummy function that ignores its arguments and
 * does nothing.  The idea is that components can always safely call
 * the function provided by this component.
 */
export default function GAProvider(props: {
    children: React.Node,
}): React.Node {
    return <context.Provider value={ga}>{props.children}</context.Provider>;
}

// This is a custom hook to return the GA client id. It returns the
// emtpy string until (and unless) it can determine that id from the GA object.
function useClientId() {
    const [clientId, setClientId] = useState<string>('');
    const ga = useContext(GAProvider.context);
    useEffect(() => {
        ga((tracker) => {
            setClientId(tracker.get('clientId'));
        });
    }, [ga]);

    return clientId;
}

// Export both the context object and the custom hook as properties
// of the GAProvider component
GAProvider.context = context;
GAProvider.useClientId = useClientId;
