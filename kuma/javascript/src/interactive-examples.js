/**
 * This file defines functions that are used to set the size of
 * interactive examples after a new page has been displayed.
 * It is based on the code in kuma/static/js/interactive.js. If
 * you make changes here, you should probably also make changes
 * in that file.
 * @flow
 */

// We use this selector to find interactive example iframes on the page.
const ieSelector = 'iframe.interactive';

// This is the origin we expect for the iframes.
const ieOrigin =
    (window && window.mdn && window.mdn.interactiveEditor.editorUrl) ||
    'https://interactive-examples.mdn.mozilla.net';

// This is our media query breakpoint. If this media query does not
// match, then we want interactive examples to use "small viewport" layout.
const mediaQuery =
    window.matchMedia && window.matchMedia('(min-width: 63.9385em)');

// This function is intended to be used as a one-time useEffect() hook
// It sets up a listener for the media query so that when we switch
// from narrow to wide or vice versa we send a signal to any
// interactive example iframes to make them change their layout.
// Because this is a useEffect() function, we could modify it to return
// a function that calls removeListener() if we decide we want to
// implement that kind of cleanup.
export function makeResponsive() {
    mediaQuery &&
        mediaQuery.addListener(function(event) {
            for (let iframe of document.querySelectorAll(ieSelector)) {
                if (iframe instanceof HTMLIFrameElement) {
                    iframe.contentWindow.postMessage(
                        { smallViewport: !event.matches },
                        ieOrigin
                    );
                }
            }
        });
}

// This function is intended as a useEffect() hook to be called
// whenever we display a new article page. If the browser width is
// narrow, it finds all interactive example iframes in the article
// and registers an onload event on them. When the load event is
// received, it uses postMessage to tell them to use a narrow layout.
export function setLayout(root: HTMLElement) {
    if (mediaQuery && !mediaQuery.matches) {
        for (let iframe of root.querySelectorAll(ieSelector)) {
            if (iframe instanceof HTMLIFrameElement) {
                // NOTE: if we just do the postMessage() right away the
                // message probably won't get through because the iframe
                // won't have loaded enough to be listening for messages.
                // So instead we wait until the iframe is ready.  It is
                // possible (though it seems unlikely) that the iframe
                // could finish loading before this effect function gets
                // called. If that happens we would miss the load event
                // and never send the message. This doesn't seem like a
                // problem in local testing, but if we don't reliably get
                // the right layout in production then we might want to
                // combine this load event handler with a setTimeout() call
                // so that we post the message on load or after 1 second.
                iframe.addEventListener('load', () => {
                    iframe.contentWindow.postMessage(
                        { smallViewport: true },
                        ieOrigin
                    );
                });
            }
        }
    }
}
