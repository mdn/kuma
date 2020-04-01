/**
 * This file exports an addLiveExampleButtons() function that is
 * intended to be run via the useEffect() hook each time we display a
 * new document in article.jsx. It looks to see if there is a "Live
 * Example" on the page, and if so, it adds the "Open in CodePen" and
 * "Open in JSFiddle" buttons to the page.
 *
 * The code in this file is a port of kuma/static/js/wiki-samples.js
 *
 * NOTE: flow is not enabled for this file because it does not work
 * well with the kind of raw HTML manipulation we're doing here.
 */
import { gettext } from './l10n.js';

const iframeSelector = '.sample-code-frame';
const tableSelector = '.sample-code-table';
const idPrefix = /^frame_/;

export function addLiveExampleButtons(rootElement) {
    let iframes = rootElement.querySelectorAll(iframeSelector);

    for (let frame of iframes) {
        // We expect the iframe to be in a section with an id related
        // to the frame id.
        let sectid = frame.id.replace(idPrefix, '');

        // It *used* to be that the ' character was allowed as a safe
        // character in IDs. We've since changed the Wiki post-processing
        // code to replace those with an empty string.
        // But to be safe, if not all legacy pages have had a chance
        // to re-render, make sure it's removed here or it'll cause
        // problems.
        // This line of code can be deleted in early 2020.
        // For context, see https://github.com/mdn/kuma/issues/5810
        sectid = sectid.replace("'", '');

        let section = document.getElementById(sectid);
        if (!section) {
            // If the section doesn't exist, then none of the selectors below
            // will work, so we can bail out early
            continue;
        }
        let sectionTitle = section.textContent;

        // Find the elements that hold the HTML, CSS and JS source code
        // We're looking for a <pre> element with a language-specific
        // class that comes after the section header. We look for both
        // direct siblings and also descendants of direct siblings
        // (because sometimes some of the source code is tucked inside
        // a hidden div).
        let html = section.querySelectorAll('pre[class*=html]');
        let css = section.querySelectorAll('pre[class*=css]');
        let js = section.querySelectorAll('pre[class*=js]');

        // Now get the source code out of those pre elements
        let htmlCode = [...html].map((p) => p.textContent).join('');
        let jsCode = [...js].map((p) => p.textContent).join('');
        let cssCode = [...css].map((p) => p.textContent).join('');

        // If we found any source code, then add buttons
        if (htmlCode || cssCode || jsCode) {
            // Add a link back to the original code as part of the HTML
            let canonical = document.querySelector('link[rel=canonical]');
            let sourceURL =
                (canonical &&
                    canonical instanceof HTMLLinkElement &&
                    canonical.href) ||
                window.location.href.split('#')[0];
            htmlCode = `<!-- Learn about this code on MDN: ${sourceURL} -->\n\n${htmlCode}`;

            // Tweak the CSS code also
            cssCode = cssCode.replace(/\xA0/g, ' '); // fixes bug 1284781

            // Create buttons
            let codepen = document.createElement('button');
            codepen.className = 'open-in-host button neutral';
            codepen.textContent = gettext('Open in CodePen');

            let jsfiddle = document.createElement('button');
            jsfiddle.className = 'open-in-host button neutral';
            jsfiddle.textContent = gettext('Open in JSFiddle');

            // And a container for the buttons
            let buttonBox = document.createElement('div');
            buttonBox.classList.add('open-in-host-container');
            buttonBox.appendChild(codepen);
            buttonBox.appendChild(jsfiddle);

            // Insert the container after the iframe or its enclosing table
            let insertButtonsAfter = frame.closest(tableSelector) || frame;
            insertButtonsAfter.insertAdjacentElement('afterend', buttonBox);

            // Finally, assign event handlers to the buttons
            codepen.onclick = function openInCodePen() {
                let div = document.createElement('div');
                div.innerHTML = `
<form method="post" action="https://codepen.io/pen/define" class="hidden" target="_blank" rel="noopener">
  <input type="hidden" name="data">
  <input type="hidden" name="utm_source" value="mdn" />
  <input type="hidden" name="utm_medium" value="code-sample" />
  <input type="hidden" name="utm_campaign" value="external-samples" />
  <input type="submit" />
</form>
`;
                let form = div.firstElementChild;
                form.data.value = JSON.stringify({
                    title: sectionTitle,
                    html: htmlCode,
                    css: cssCode,
                    js: jsCode,
                });
                document.body.appendChild(form);
                form.submit();

                // TODO: the old code in wiki-samples.js also sets GA
                // dimension8 to Yes at this point, but never actually
                // sends the data to Google, so I have not ported that.
                if (window && window.mdn && window.mdn.analytics) {
                    window.mdn.analytics.trackEvent({
                        category: 'Samples',
                        action: 'open-codepen',
                        label: sectid,
                    });
                }
            };

            jsfiddle.onclick = function openInJSFiddle() {
                let div = document.createElement('div');
                div.innerHTML = `
<form method="post" action="https://jsfiddle.net/api/mdn/" class="hidden" target="_blank" rel="noopener">
  <input type="hidden" name="html" />
  <input type="hidden" name="css" />
  <input type="hidden" name="js" />
  <input type="hidden" name="title" />
  <input type="hidden" name="wrap" value="b" />
  <input type="hidden" name="utm_source" value="mdn" />
  <input type="hidden" name="utm_medium" value="code-sample" />
  <input type="hidden" name="utm_campaign" value="external-samples" />
  <input type="submit" />
</form>
`;
                let form = div.firstElementChild;
                form.html.value = htmlCode;
                form.css.value = cssCode;
                form.js.value = jsCode;
                form.title.value = sectionTitle;
                document.body.appendChild(form);
                form.submit();

                // TODO: the old code in wiki-samples.js also sets GA
                // dimension8 to Yes at this point, but never actually
                // sends the data to Google, so I have not ported that.
                if (window && window.mdn && window.mdn.analytics) {
                    window.mdn.analytics.trackEvent({
                        category: 'Samples',
                        action: 'open-jsfiddle',
                        label: sectid,
                    });
                }
            };
        }
    }
}
