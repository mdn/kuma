/**
 * Error classes that can be thown when trying to render the macros on a page.
 * @prettier
 */

/**
 * This is the common superclass of the other error classes here.
 * It includes the code for excerpting the portion of the document that the
 * error occurs in and drawing an ASCII art arrow to point at it.
 */
class SourceCodeError extends Error {
    constructor(cause, line, column, name) {
        super();
        this.cause = cause;
        this.line = line;
        this.column = column;
        this.stack = cause.stack;

        // Kuma's error handling code seems to expect the macro name here.
        // See server.js and firelogger.js for details.
        if (name) {
            this.options = { name };
        }
    }

    getSourceContext(source) {
        function arrow(column) {
            let arrow = '';
            for (let i = 0; i < column + 7; i++) {
                arrow += '-';
            }
            return arrow + '^';
        }

        function formatLine(i, line) {
            let lnum = ('      ' + (i + 1)).substr(-5);
            return lnum + ' | ' + line;
        }

        let lines = source.split('\n');

        // Work out a range of lines to show for context around the error,
        // 2 before and after.
        let errorLine = this.line - 1;
        let startLine = Math.max(errorLine - 2, 0);
        let endLine = Math.min(errorLine + 3, lines.length);

        // Assemble the lines of error context, inject the column pointer
        // at the appropriate spot after the error line.
        var context = [];
        for (var i = startLine; i < endLine; i++) {
            context.push(formatLine(i, lines[i]));
            if (i == errorLine) {
                context.push(arrow(this.column));
            }
        }
        return context.join('\n');
    }
}

/**
 * A MacroInvocationError is thrown if we can't parse the HTML document
 * because it uses incorrect syntax for invoking macros. In this case
 * the error object is from the parser class and tells us the location
 * of the error.
 */
class MacroInvocationError extends SourceCodeError {
    constructor(error, source) {
        // If the error is not a SyntaxError, with a location property then
        // just return it instead of creating a wrapper object
        if (error.name !== 'SyntaxError' || error.location === undefined) {
            return error;
        }

        super(error, error.location.start.line, error.location.start.column);
        this.name = 'MacroInvocationError';

        // Finally, assemble the complete error message.
        this.message = `Syntax error at line ${this.line}, column ${
            this.column
        } of document:\n${this.getSourceContext(source)}\n${error.message}`;
    }
}

/**
 * A MacroNotFoundError is thrown when an HTML document uses
 * a macro that does not exist. The error message shows the location of the
 * macro in the HTML document, which it determines from the token argument.
 */
class MacroNotFoundError extends SourceCodeError {
    constructor(error, source, token) {
        super(
            error,
            token.location.start.line,
            token.location.start.column,
            token.name
        );
        this.name = 'MacroNotFoundError';

        // Finally, assemble the complete error message.
        this.message = `Unknown macro '${token.name}' at line ${
            this.line
        }, column ${this.column} of document:\n${this.getSourceContext(
            source
        )}`;
    }
}

/**
 * A MacroCompilationError is thrown when there is an exception during
 * template compilation. The error message shows the location of the
 * macro in the HTML document and also includes the underlying error message.
 */
class MacroCompilationError extends SourceCodeError {
    constructor(error, source, token) {
        super(
            error,
            token.location.start.line,
            token.location.start.column,
            token.name
        );
        this.name = 'MacroCompilationError';

        // Finally, assemble the complete error message.
        this.message = `Error compiling macro '${token.name}' at line ${
            this.line
        }, column ${this.column} of document:\n${this.getSourceContext(
            source
        )}\n${error.message};`;
    }
}

/**
 * A MacroExecutionError is thrown when there is an exception during
 * template rendering. The error message shows the location of the
 * macro in the HTML document and also includes the error message
 * from the underlying runtime error.
 */
class MacroExecutionError extends SourceCodeError {
    constructor(error, source, token) {
        super(
            error,
            token.location.start.line,
            token.location.start.column,
            token.name
        );
        this.name = 'MacroExecutionError';

        // Finally, assemble the complete error message.
        this.message = `Error rendering macro '${token.name}' at line ${
            this.line
        }, column ${this.column} of document:\n${this.getSourceContext(
            source
        )}\n${error.message};`;
    }
}

module.exports = {
    MacroInvocationError,
    MacroNotFoundError,
    MacroCompilationError,
    MacroExecutionError
};
