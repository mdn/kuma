/**
 * @prettier
 */

const Parser = require('../src/parser.js');

describe('Parser', function() {
    it('input with no macros', () => {
        let input = '<p>This is a test.\n<h1>Hello world!</h1>';
        expect(Parser.parse(input)).toEqual([
            {
                type: 'TEXT',
                chars: input
            }
        ]);
    });

    it('one macro, embedded in text', () => {
        expect(Parser.parse('foo {{bar}}\nbaz')).toEqual([
            {
                type: 'TEXT',
                chars: 'foo '
            },
            {
                type: 'MACRO',
                name: 'bar',
                args: [],
                location: {
                    start: { line: 1, column: 5, offset: 4 },
                    end: { line: 1, column: 12, offset: 11 }
                }
            },
            {
                type: 'TEXT',
                chars: '\nbaz'
            }
        ]);
    });

    it('macro with numeric arguments', () => {
        expect(Parser.parse('{{bar(0,1,2.2)}}')).toEqual([
            {
                type: 'MACRO',
                name: 'bar',
                args: ['0', '1', '2.2'],
                location: {
                    start: { line: 1, column: 1, offset: 0 },
                    end: { line: 1, column: 17, offset: 16 }
                }
            }
        ]);
    });

    it('macro with string arguments', () => {
        expect(Parser.parse('{{bar(\'zero\',"one")}}')).toEqual([
            {
                type: 'MACRO',
                name: 'bar',
                args: ['zero', 'one'],
                location: {
                    start: { line: 1, column: 1, offset: 0 },
                    end: { line: 1, column: 22, offset: 21 }
                }
            }
        ]);
    });

    it('string arguments can contain parens and braces', () => {
        expect(Parser.parse('{{bar(\')}}"\',"\')}}")}}')).toEqual([
            {
                type: 'MACRO',
                name: 'bar',
                args: [')}}"', "')}}"],
                location: {
                    start: { line: 1, column: 1, offset: 0 },
                    end: { line: 1, column: 23, offset: 22 }
                }
            }
        ]);
    });

    it('whitespace is ignored', () => {
        let input = '{{ \n \t bar(\'zero\', \n\t "one" ) \n\t }}';
        expect(Parser.parse(input)).toEqual([
            {
                type: 'MACRO',
                name: 'bar',
                args: ['zero', 'one'],
                location: {
                    start: { line: 1, column: 1, offset: 0 },
                    end: { line: 4, column: 5, offset: 35 }
                }
            }
        ]);
    });

    it('JSON values are parsed correctly', () => {
        'use strict';
        let input =
            '{{ f({ "a": "x", "b": -1e2, "c": 0.5, "d": [1,2, 3], "e":true, "f":false }) }}';
        expect(Parser.parse(input)).toEqual([
            {
                type: 'MACRO',
                name: 'f',
                args: [
                    {
                        a: 'x',
                        b: -1e2,
                        c: 0.5,
                        d: [1, 2, 3],
                        e: true,
                        f: false
                    }
                ],
                location: {
                    start: { line: 1, column: 1, offset: 0 },
                    end: { line: 1, column: 79, offset: 78 }
                }
            }
        ]);
    });

    it('JSON parameter should allow a single-item list', () => {
        'use strict';
        var tokens = Parser.parse('{{ f({ "a": ["one"] }) }}');
        expect(tokens).toEqual([
            {
                type: 'MACRO',
                name: 'f',
                args: [{ a: ['one'] }],
                location: {
                    start: { line: 1, column: 1, offset: 0 },
                    end: { line: 1, column: 26, offset: 25 }
                }
            }
        ]);
    });

    describe('Invalid JSON should cause a syntax error', () => {
        'use strict';

        it('Quotes around property names are required', () => {
            expect(() => {
                Parser.parse('{{ f({ x: 1 }) }}');
            }).toThrow();
        });

        it('Octal literals are not allowed', () => {
            expect(() => {
                Parser.parse('{{ f({ "x": 01 }) }}');
            }).toThrow();
        });

        it('Trailing commas are not allowed', () => {
            expect(() => {
                Parser.parse('{{ f({ "x": [1,] }) }}');
            }).toThrow();
        });
    });

    it("JSON strings should be able to contain ')'", () => {
        'use strict';
        var tokens = Parser.parse('{{ f({ "a": "f)" }) }}');
        expect(tokens).toEqual([
            {
                type: 'MACRO',
                name: 'f',
                args: [{ a: 'f)' }],
                location: {
                    start: { line: 1, column: 1, offset: 0 },
                    end: { line: 1, column: 23, offset: 22 }
                }
            }
        ]);
    });

    it('Empty JSON values are allowed', () => {
        'use strict';
        var tokens = Parser.parse('{{ f({}) }}');
        expect(tokens).toEqual([
            {
                type: 'MACRO',
                name: 'f',
                args: [{}],
                location: {
                    start: { line: 1, column: 1, offset: 0 },
                    end: { line: 1, column: 12, offset: 11 }
                }
            }
        ]);

        tokens = Parser.parse('{{ f({ "a": [] }) }}');
        expect(tokens).toEqual([
            {
                type: 'MACRO',
                name: 'f',
                args: [{ a: [] }],
                location: {
                    start: { line: 1, column: 1, offset: 0 },
                    end: { line: 1, column: 21, offset: 20 }
                }
            }
        ]);
    });

    describe('Escaped unicode codepoints are parsed correctly', () => {
        'use strict';

        it('Lowercase', () => {
            expect(Parser.parse('{{ f({ "a": "\\u00f3" }) }}')).toEqual([
                {
                    type: 'MACRO',
                    name: 'f',
                    args: [{ a: '\u00f3' }],
                    location: {
                        start: { line: 1, column: 1, offset: 0 },
                        end: { line: 1, column: 27, offset: 26 }
                    }
                }
            ]);
        });

        it('Uppercase', () => {
            expect(Parser.parse('{{ f({ "a": "\\u00F3" }) }}')).toEqual([
                {
                    type: 'MACRO',
                    name: 'f',
                    args: [{ a: '\u00f3' }],
                    location: {
                        start: { line: 1, column: 1, offset: 0 },
                        end: { line: 1, column: 27, offset: 26 }
                    }
                }
            ]);
        });

        it('Non-hexadecimal characters are not allowed', () => {
            expect(() => {
                Parser.parse('{{ f({ "a": "\\uGHIJ" }) }}');
            }).toThrow();
        });

        it('Four digits are required', () => {
            expect(() => {
                Parser.parse('{{ f({ "a": "\\uFF" }) }}');
            }).toThrow();
        });
    });
});
