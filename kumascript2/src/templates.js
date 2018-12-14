/**
 * The Templates class is a thin wrapper around the EJS templating system.
 *
 * Given a directory in the local filesystem, it finds all .js and .ejs files
 * under that directory and assumes that they are all valid EJS templates.
 * It uses the lowercase filename, with path and extension removed as
 * a unique identifier for the macro. (The constructor raises an error
 * if macro names are not unique within the directory.)
 *
 * The render() method takes the name of a template and an object of arguments
 * and renders the named template with those arguments. render() is declared
 * async, so it returns Promise<string> rather than returning a string
 * directly, which supports templates that are themselves async.
 *
 * render() relies on EJS's built-in caching and file-loading capabilities
 * so no template should ever be loaded or compiled more than once.
 *
 * The getTemplateMap() function returns a Map object that maps template names
 * to the name of the file that implements the template.
 *
 * @prettier
 */
const fs = require('fs');
const path = require('path');
const ejs = require('ejs');

class Templates {
    constructor(macroDirectory) {
        this.macroDirectory = macroDirectory;
        this.macroNameToPath = new Map();

        // Find all the macros in the macros dir and build a map
        // from macro name to filename
        const dirs = [macroDirectory];
        const duplicates = new Map();

        // Walk the directory tree under the specified root directory.
        while (dirs.length > 0) {
            let dir = dirs.shift();
            fs.readdirSync(dir).forEach(fn => {
                // If the given filename is a directory, push it onto
                // the queue, otherwise consider it a template.
                let fp = path.join(dir, fn);
                if (fs.statSync(fp).isDirectory()) {
                    dirs.push(fp);
                } else if (
                    fp.endsWith('.js') ||
                    fp.endsWith('.ejs') ||
                    fp.endsWith('.json')
                ) {
                    var name = path.parse(fn).name.toLowerCase();
                    if (this.macroNameToPath.has(name)) {
                        // Keep track of all duplicates and throw error later.
                        if (!duplicates.has(name)) {
                            duplicates.set(name, [
                                this.macroNameToPath.get(name)
                            ]);
                        }
                        duplicates.get(name).push(fp);
                    } else {
                        this.macroNameToPath.set(name, fp);
                    }
                }
            });
        }

        if (this.macroNameToPath.size === 0) {
            // Let's throw an error if no macros could be discovered, since
            // for now this is the only time we check and this loader is
            // useless if there are no macros.
            throw new Error(`No macros found in "${macroDirectory}"`);
        }

        if (duplicates.size !== 0) {
            // Duplicate template names
            var msg = 'Duplicate macros:';
            for (let [name, files] of duplicates) {
                msg += '\n' + name + ': ' + files.join(', ');
            }
            throw new Error(msg);
        }
    }

    async render(name, args) {
        // Normalize the macro name by converting colons to hyphens and
        // uppercase letters to lowercase.
        name = name.replace(/:/g, '-').toLowerCase();
        let path = this.macroNameToPath.get(name);
        if (!path) {
            // There is code in render.js that catches this error and
            // creates a more informative MacroNotFoundError
            throw new ReferenceError(`Unknown macro ${name}`);
        }

        let rendered = await ejs.renderFile(path, args, {
            cache: true,
            async: true
        });
        return rendered.trim();
    }

    getTemplateMap() {
        return new Map(this.macroNameToPath);
    }
}

module.exports = Templates;
