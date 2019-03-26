// @flow
import * as React from 'react';
import { useState, useEffect } from 'react';

export type DocumentData = {
    locale: string,
    slug: string,
    id: number,
    title: string,
    summary: string,
    absoluteURL: string,
    redirectURL: string,
    editURL: string,
    bodyHTML: string,
    quickLinksHTML: string,
    tocHTML: string,
    parents: Array<{ url: string, title: string }>,
    translations: Array<{ locale: string, url: string, title: string }>
};

const context = React.createContext<DocumentData | null>(null);

type DocumentProviderProps = {
    children: React.Node,
    initialDocumentData: DocumentData
};

export default function DocumentProvider(
    props: DocumentProviderProps
): React.Node {
    const [documentData, setDocumentData] = useState(props.initialDocumentData);

    if (!document.body) {
        throw new Error('DocumentProvider rendered before a body exists.');
    }
    const body = document.body;

    // A one-time effect that runs only on mount, to set up
    // an event handler for client-side navigation
    useEffect(() => {
        function navigate(url, localeAndSlug) {
            body.style.opacity = '0.15';
            fetch(`/api/v1/doc/${localeAndSlug}`)
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        // If we didn't get a good response, throw an error
                        // that we'll handle in the catch() function below.
                        throw new Error(
                            `${response.status}:${response.statusText}`
                        );
                    }
                })
                .then(json => {
                    window.scrollTo(0, 0);
                    setDocumentData(json);
                    body.style.opacity = '1';
                })
                .catch(() => {
                    // If anything went wrong (most likely a 404 from
                    // the document API), we give up on client-side nav
                    // and just try loading the page. This might allow
                    // error recovery or will at least show the user
                    // a real 404 page.
                    window.location = url;
                });
        }

        body.addEventListener('click', (e: MouseEvent) => {
            // If this is not a left click, or not a single click, or
            // if there are modifier keys, then this is not a simple
            // navigation that we can do on the client side, so do nothing.
            // Also if it was not a click on an HTMLElement, do nothing.
            if (
                e.button !== 0 ||
                e.detail > 1 ||
                e.altKey ||
                e.ctrlKey ||
                e.metaKey ||
                e.shiftKey ||
                !(e.target instanceof HTMLElement)
            ) {
                return;
            }

            // Find the closest enclosing <a> element
            let link = e.target.closest('a');

            // If the link is null, or is not actually an HTMLAnchorElement
            // or it does not have an href, or if the href includes
            // a hash, or if it is an off-site link, then we can't client
            // side navigate and should just return.
            if (
                !(link instanceof HTMLAnchorElement) ||
                !link.href ||
                link.hash ||
                link.origin !== window.location.origin
            ) {
                return;
            }

            let url = link.href;
            let parts = link.pathname.split('/');
            if (parts[2] !== 'docs') {
                return;
            }

            e.preventDefault();

            let locale = parts[1];
            let slug = parts.slice(3).join('/');
            let localeAndSlug = `${locale}/${slug}`;
            history.pushState(
                { url, localeAndSlug },
                '',
                url
            );
            navigate(url, localeAndSlug);
        });

        window.addEventListener('popstate', event => {
            if (event.state) {
                navigate(event.state.url, event.state.localeAndSlug);
            }
        });
    }, []);

    return (
        <context.Provider value={documentData}>
            {props.children}
        </context.Provider>
    );
}

DocumentProvider.context = context;
