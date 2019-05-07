// @flow
import * as React from 'react';

type GAOptions = { [string]: any };
type GAFunction = (
    string,
    string | GAOptions,
    ...Array<string | number | GAOptions>
) => void;

const noop: GAFunction = () => {};

const context = React.createContext<GAFunction>(noop);

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
    children: React.Node
}): React.Node {
    let ga: GAFunction;

    // If there is a window object that defines a ga() function, then
    // that ga function is the value we will provide. Otherwise we just
    // provide a dummy function that does nothing.
    if (typeof window === 'object' && typeof window.ga === 'function') {
        ga = window.ga;
    } else {
        ga = noop;
    }

    return <context.Provider value={ga}>{props.children}</context.Provider>;
}

GAProvider.context = context;
