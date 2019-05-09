// @flow
import * as React from 'react';

const context = React.createContext<string>('en-US');

// This component is a context provider that makes the current locale
// available to any components that need it. This is the locale that
// appears in the browser location bar. We need a provider for it,
// however because when we're rendering on the server, we can't just
// look at window.location.pathname to extract the locale. Note also
// that when documents are not translated, we return the english
// version and this means that the locale in the URL (which is the
// value provided by this component) may differ from the locale of the
// document that is displayed.
export default function LocaleProvider(props: {
    locale: string,
    children: React.Node
}): React.Node {
    return (
        <context.Provider value={props.locale}>
            {props.children}
        </context.Provider>
    );
}

LocaleProvider.context = context;
