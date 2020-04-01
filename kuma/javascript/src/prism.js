/**
 * This file defines a highlightSyntax() function that article.jsx
 * uses as an effect hook to highlight code samples each time we
 * display a new article. The code in this file does not do any code
 * formatting itself. It simply finds the <pre> elements in the
 * article and puts them in the format expected by the Prism code
 * formatter. We assume that window.Prism is defined.
 *
 * TODO: we should dynamically load the Prism code when it is first used.
 *
 * This code is based on the code in static/js/syntax-prism.js
 * This version is a port that removes jQuery calls. If you change
 * this file, you should probably also change that original one.
 *
 * @flow
 */

let initialized = false;

export function highlightSyntax(root: HTMLElement) {
    // If the Prism module is not here, there is nothing we can do
    if (typeof window === 'undefined' || !window.Prism) {
        return;
    }

    // Flow is not comfortable with undeclared global symbols
    const Prism = window.Prism;

    // Set up Prism the first time we're called.
    if (!initialized) {
        initialized = true;

        // Define some language aliases
        let languages = Prism.languages;
        languages.xml = languages.xul = languages.html = languages.markup;
        languages.js = languages.javascript;
        languages.cpp = languages.clike;
    }

    // Loop through all <pre> blocks within the root (article) element
    // tweaking them so that they use proper Prism classes and attributes.
    for (let block of root.querySelectorAll('pre')) {
        // Exclude syntax boxes from this pre-processing
        if (
            block.classList.contains('syntaxbox') ||
            block.classList.contains('twopartsyntaxbox')
        ) {
            continue;
        }

        // Expect each block to have a single text node child which
        // holds the code to be highlighted. If there is is more than
        // one child or if it is not a text node, then assume that the
        // block is already formatted and does not need to be tweaked.
        if (
            block.childNodes.length !== 1 ||
            block.childNodes[0].nodeType !== Node.TEXT_NODE
        ) {
            continue;
        }

        // If a block does not specify a language, assume HTML highlighting.
        let language = 'html';

        // MDN documents refer to the syntax highlight language as
        // a "brush", and encode it for a <pre> element with
        // "brush:<lang>" or "brush: <lang>" in the class attribute.
        // We can extract the desired language from the attribute.
        let match = block.className.match(/brush: ?(\w+)/);
        if (match && match[1]) {
            language = match[1].toLowerCase();
            // Don't ask for languages that our Prism build does not support.
            if (!(language in Prism.languages)) {
                language = '';
            }
        }

        // If the author did not explicitly turn off line numbers
        // then ask Prism to add line numbers for us
        if (!block.classList.contains('no-line-numbers')) {
            block.classList.add('line-numbers');
        }

        // Do we need to highlight any lines?
        // Legacy format: highlight:[8,9,10,11,17,18,19,20]
        let lines = block.className.match(/highlight:? ?\[(.*)\]/);
        if (lines && lines[1]) {
            block.setAttribute('data-line', lines[1]);
        }

        // Finally, add a <code> element to the block and specify the
        // highlight language on that element. Then reparent the code text
        // into that code element. We know from the check above that
        // the code is a single text node at block.childNodes[0])
        let code = document.createElement('code');
        if (language) {
            code.classList.add(`language-${language}`);
        }
        block.appendChild(code);
        code.appendChild(block.childNodes[0]);
    }

    // Now that we've fixed up the code blocks, ask Prism to highlight them
    Prism.highlightAll();
}
