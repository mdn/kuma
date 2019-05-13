// @flow
import * as React from 'react';
import { useContext, useEffect, useState } from 'react';

import GAProvider from './ga-provider.jsx';
import LocaleProvider from './locale-provider.jsx';

export type DocumentData = {
    locale: string,
    slug: string,
    enSlug: string, // For non-english documents, the original english slug
    id: number,
    title: string,
    summary: string,
    absoluteURL: string,
    editURL: string,
    bodyHTML: string,
    quickLinksHTML: string,
    tocHTML: string,
    parents: Array<{ url: string, title: string }>,
    translations: Array<{
        locale: string,
        language: string,
        localizedLanguage: string,
        url: string,
        title: string
    }>,
    contributors: Array<string>,
    lastModified: string, // An ISO date
    lastModifiedBy: string
};

const context = React.createContext<DocumentData | null>(null);

type DocumentProviderProps = {
    children: React.Node,
    initialDocumentData: DocumentData
};

export default function DocumentProvider(
    props: DocumentProviderProps
): React.Node {
    const locale = useContext(LocaleProvider.context);
    const [documentData, setDocumentData] = useState(props.initialDocumentData);
    const ga = useContext(GAProvider.context);

    // A one-time effect that runs only on mount, to set up
    // an event handler for client-side navigation
    useEffect(() => {
        if (!document.body) {
            throw new Error('DocumentProvider effect ran without body.');
        }
        const body = document.body;

        // This is the function that does client side navigation
        function navigate(url, slug) {
            body.style.opacity = '0.15';
            fetch(`/api/v1/doc/${locale}/${slug}`, { redirect: 'follow' })
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
                    if (json.redirectURL) {
                        // We've got a redirect to a document that can't be
                        // handled via the /api/v1/doc/ API, so we just do a
                        // full page load of that document.
                        window.location = json.redirectURL;
                    } else {
                        let documentData = json.documentData;
                        // If the slug of the received document is different
                        // than the slug we requested, then we were redirected
                        // and we need to fix up the URL in the location bar
                        if (documentData.slug !== slug) {
                            history.replaceState(
                                {
                                    url: documentData.absoluteURL,
                                    slug: documentData.slug
                                },
                                '',
                                documentData.absoluteURL
                            );
                        }

                        window.scrollTo(0, 0);
                        setDocumentData(documentData);
                        body.style.opacity = '1';

                        // Tell Google Analytics about this navigation.
                        // We use 'dimension19' to mean client-side navigate
                        ga('set', 'dimension19', 'Yes');

                        // If the document data includes enSlug, or if the
                        // document is in english, then pass the slug to
                        // google analytics as dimension 17.
                        if (documentData.enSlug) {
                            ga('set', 'dimension17', documentData.enSlug);
                        } else if (documentData.locale === 'en-US') {
                            ga('set', 'dimension17', documentData.slug);
                        }

                        ga('send', 'pageload');
                    }
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

        // A click event handler that triggers client-side navigation
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

            // If the link is not to a /docs/ URL then we can't handle
            // it via client-side navigation.
            if (parts[2] !== 'docs') {
                return;
            }

            // If the locale in the URL is not the same as the current
            // locale then we can't do client-side navigation because
            // we don't have the right strings loaded.
            if (parts[1] !== locale) {
                return;
            }

            // If we get here, then we should be good-to-go for client
            // side navigation. Calling preventDefault() ensures that the
            // browser will not actually follow the link.
            e.preventDefault();

            let slug = parts.slice(3).join('/');
            history.pushState({ url, slug }, '', url);
            navigate(url, slug);
        });

        // An event handler that does client-side navigation in response
        // to the back and forward buttons
        window.addEventListener('popstate', event => {
            if (event.state) {
                navigate(event.state.url, event.state.slug);
            }
        });

        // Finally, after registering those event handlers, we also need
        // to use history.pushState() to record the URL of the initial page
        // that just loaded so that the user can return to it via the
        // back button.
        history.pushState(
            {
                url: window.location.href,
                slug: window.location.pathname
                    .split('/')
                    .slice(3) // strip "/<locale>/docs/"
                    .join('/')
            },
            '',
            window.location.href
        );
    }, []);

    return (
        <context.Provider value={documentData}>
            {props.children}
        </context.Provider>
    );
}

DocumentProvider.context = context;
