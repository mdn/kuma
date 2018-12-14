/**
 * @prettier
 */

const Templates = require('../src/templates.js');

describe('Templates class', () => {
    it('has the expected methods', () => {
        expect(typeof Templates).toBe('function');
        expect(Templates.prototype.render).toBeInstanceOf(Function);
        expect(Templates.prototype.getTemplateMap).toBeInstanceOf(Function);
    });

    function dir(name) {
        return `${__dirname}/fixtures/macros.test/${name}`;
    }

    it('throws on non-existent dir', () => {
        expect(() => new Templates(dir('no_such_directory'))).toThrow(
            'no such file or directory'
        );
    });

    it('throws on an empty dir', () => {
        expect(() => new Templates(dir('empty_macro_dir'))).toThrow(
            'No macros found'
        );
    });

    it('throws on duplicate macros', () => {
        expect(() => new Templates(dir('duplicate_macros'))).toThrow(
            'Duplicate macros'
        );
    });

    it('creates a macros map', () => {
        let directory = dir('macros');
        let macros = new Templates(directory);
        expect(macros.getTemplateMap()).toEqual(
            new Map([
                ['test1', directory + '/test1.ejs'],
                ['test2', directory + '/Test2.ejs'],
                ['async', directory + '/async.ejs']
            ])
        );
    });

    it('can render macros', async () => {
        let macros = new Templates(dir('macros'));

        let result1 = await macros.render('test1', {});
        expect(result1).toEqual('1');

        let result2 = await macros.render('test2', { n: 2 });
        expect(result2).toEqual('3');
    });

    it('macros can use await', async () => {
        let macros = new Templates(dir('macros'));

        let result = await macros.render('async', {
            async_adder: function(n) {
                return new Promise((resolve, reject) => {
                    setTimeout(() => resolve(n + 1));
                });
            }
        });
        expect(result).toEqual('2\n3');
    });

    it('macro arguments can be inherited', async () => {
        let macros = new Templates(dir('macros'));
        let result = await macros.render('test2', Object.create({ n: 2 }));
        expect(result).toEqual('3');
    });

    it('only loads files once', async () => {
        const EJS = require('ejs');
        const mockLoader = jest.fn(filename => `<%= "${filename}" -%>`);
        EJS.clearCache();
        EJS.fileLoader = mockLoader;
        const directory = dir('macros');
        const macros = new Templates(directory);

        let result1 = await macros.render('test1');
        expect(result1).toBe(directory + '/test1.ejs');
        expect(mockLoader.mock.calls.length).toBe(1);

        let result2 = await macros.render('test2');
        expect(result2).toBe(directory + '/Test2.ejs');
        expect(mockLoader.mock.calls.length).toBe(2);

        // Render the macros again, but don't expect any more loads
        await macros.render('test1');
        await macros.render('test2');
        await macros.render('test1');
        await macros.render('test2');
        expect(mockLoader.mock.calls.length).toBe(2);
    });
});
