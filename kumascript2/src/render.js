/**
 * The render() method of a Page object takes as input a string of
 * text containing embedded KumaScript macros and asynchronously
 * returns a string in which the embedded macros have been
 * expanded. The Page object does not include any asynchronous
 * code, but macros may be asynchronous (they can make HTTP requests,
 * and use `await` for example), so the render() method is declared
 * `async`.
 *
 * Macros are embedded in source documents within pairs of curly
 * braces {{...}}.  The Parser object of parser.js is used to extract
 * macro invocations (which can include arguments) and strings of
 * constant text from the source document.
 *
 * A Templates object (which represents a directory of EJS templates) is
 * used to render individual macros. The path to the macros directory is
 * specified when the Page object is created.
 *
 * When a macro is rendered, it takes a context or namespace object that
 * defines the values available to the macro. These values come from three
 * sources:
 *
 *   1) A context object passed to the the Page() constructor.
 *      This object defines bindings that are univerally available
 *
 *   2) A context object passed to the render() method. This object
 *      defines bindings available for a single invocation only, and we
 *      use it for bindings that are specific to a single web request
 *      for example.
 *
 *   3) An object that represents the arguments (if any) for a single
 *      macro invocation. These are values that appear in the source
 *      document as part of the macro, and are bound to names $0, $1, etc.
 *
 * @prettier
 */
const Parser = require('./parser.js');
const Environment = require('./environment.js');
const {
    MacroInvocationError,
    MacroNotFoundError,
    MacroCompilationError,
    MacroExecutionError
} = require('./errors.js');

async function render(source, templates, pageEnvironment) {
    // Parse the source document.
    let tokens;
    try {
        tokens = Parser.parse(source);
    } catch (e) {
        // If there are any parsing errors in the input document
        // we can't process any of the macros, and just return the
        // source document unmodified, along with the error.
        // Note that rendering errors in the macros are different;
        // we handle these individually below.
        return [source, [new MacroInvocationError(e, source)]];
    }

    // Create the Environment object that we'll use to render all of
    // the macros on the page
    let environment = new Environment(pageEnvironment, templates);

    // Loop through the tokens, rendering the macros and collecting
    // the resulting promises. We detect duplicate invocations and
    // only render those once, on the assumption that their output will
    // be the same each time. (This is an important optimization for
    // xref macros, for example, since they can make asynchronous
    // network requests, and documents often have duplicate xrefs.)
    let promises = [];
    let signatureToPromiseIndex = new Map();

    // Keep track of errors that occur when rendering the macros.
    let errors = [];

    // Loop through the tokens
    for (let token of tokens) {
        // We only care about macros; skip anything else
        if (token.type !== 'MACRO') {
            continue;
        }

        // Check to see if we're already processing this exact
        // macro invocation. To do that we need a signature for
        // the macro. When the macro has json arguments we want to
        // ignore their order, so we do some tricky stringification
        // here in that case.
        if (token.args.length === 1 && typeof token.args[0] === 'object') {
            // the json args case
            let keys = Object.keys(token.args[0]);
            keys.sort();
            token.signature = token.name + JSON.stringify(token.args[0], keys);
        } else {
            // the regular case: args is just an array of strings
            token.signature = token.name + JSON.stringify(token.args);
        }

        // If this signature is already in the signature map, then we're
        // already running the macro and don't need to do anything here.
        if (signatureToPromiseIndex.has(token.signature)) {
            continue;
        }

        // Now start rendering his macro. Most macros are
        // synchronous and very fast, but some may make network
        // requests, so we treat them all as async and build up an
        // array of promises.  Note that we will await on the
        // entire array, not on each promise individually. That
        // allows the macros to execute in parallel. We map this
        // macro's signature to the index of its promise in the
        // array so that later we can find the output for each
        // macro.
        let index = promises.length;
        signatureToPromiseIndex.set(token.signature, index);
        errors.push(null);
        promises.push(
            templates
                .render(token.name, environment.getExecutionContext(token.args))
                .catch(e => {
                    // If there was an error rendering this macro, we still want
                    // the promise to resolve normally because otherwise the
                    // Promise.all() will fail. So we resolve to "", and store
                    // the error in the errors array.
                    if (
                        e instanceof ReferenceError &&
                        e.message.startsWith('Unknown macro')
                    ) {
                        // The named macro does not exist
                        errors[index] = new MacroNotFoundError(
                            e,
                            source,
                            token
                        );
                    } else if (e.name === 'SyntaxError') {
                        // There was a syntax error compiling the macro
                        errors[index] = new MacroCompilationError(
                            e,
                            source,
                            token
                        );
                    } else {
                        // There was a runtime error executing the macro
                        errors[index] = new MacroExecutionError(
                            e,
                            source,
                            token
                        );
                    }
                    return '';
                })
        );
    }

    // Now wait for all the promises to finish
    let results = await Promise.all(promises);

    // And assemble the output document
    let output = tokens
        .map(token => {
            if (token.type === 'TEXT') {
                return token.chars;
            } else if (token.type === 'MACRO') {
                let promiseIndex = signatureToPromiseIndex.get(token.signature);
                if (errors[promiseIndex]) {
                    // If there was an error rendering this macro, then we
                    // just use the original macro source text for the output
                    return source.slice(
                        token.location.start.offset,
                        token.location.end.offset
                    );
                }
                return results[promiseIndex];
            }
        })
        .join('');

    // The return value is the rendered string plus an array of errors.
    return [output, errors.filter(e => e !== null)];
}

module.exports = render;
