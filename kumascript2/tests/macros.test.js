/**
 * Verify that all of the macros in ../macros/ compile without errors
 *
 * @prettier
 */
const fs = require('fs');
const ejs = require('ejs');
const Templates = require('../src/templates.js');

describe('macros/ directory', () => {
    describe('compile all macros', () => {
        let templates = new Templates(`${__dirname}/../macros`);
        let templateMap = templates.getTemplateMap();
        macroNames = Array.from(templateMap.keys());

        it.each(macroNames)('%s', macro => {
            let filename = templateMap.get(macro);
            let source = fs.readFileSync(filename, 'utf-8');
            ejs.compile(source, { async: true });
        });
    });
});
