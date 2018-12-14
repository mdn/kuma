/*
 * PEG.js parser for macros in wiki documents.
 * see also: http://pegjs.majda.cz/documentation
 */
start = Document

Document = ( Text / Macro )+

Text = c:Chars+ {
    return {
        type: "TEXT",
        chars: c.join('')
    };
}

Chars = c:( DoubleRightBrace / SingleLeftBrace / SingleRightBrace /
            EscapedBraces / SingleBackslash /
            BoringChars ) { return c.join(''); }

/* This seems like a horrible pile of hacks, but works. */
SingleLeftBrace = "{" [^{]
SingleRightBrace = "}" [^}]
DoubleRightBrace = c:"}}" { return [c]; }
EscapedBraces = c:("\\{" / "\\}") { return [c[1]]; }
SingleBackslash = "\\" { return ["\\"]; }
BoringChars = [^{}\\]+

Macro = "{{" __ name:MacroName __ args:(Arguments / ArgumentsJSON)? __ "}}" { 
    return {
        type: 'MACRO',
        name: name.join(''),
        args: args || [],
        location: location()
    };
}

/* Trying to be inclusive, but want to exclude params start and macro end */
MacroName = [^\(\} ]+

Arguments
  = "(" __ args:ArgumentList? __ ")" { return args; }

ArgumentsJSON
  = "(" __ &"{" json_args:JSONArgument __ ")" {
        try {
            return [JSON.parse(json_args)];
        } catch (e) {
            // Try to provide better diagnostics than
            // "Syntax error at line , column" using PEG's internal APIs.
            var errorPosition = computeErrorPosition();
            throw new PEG.parser.SyntaxError(
              ["valid JSON object as the parameter of the preceding macro"],
              json_args.join(''),
              offset,
              errorPosition.line,
              errorPosition.column
            );
        }
    }

JSONArgument
  = obj:JSONObject {
      // Transform the parse tree back into a string.
      function flatten(x) {
      //      console.log("Flatten:", typeof x, x);
        if (typeof x === "string") {
          return x;
        } else if (x === null) {
          return '';
        } else {
          return x.map(flatten).join('');
        }
          //        return Array.prototype.map.call(x, flatten).join('');
      }
      return flatten(obj);
    }

JSONObject
  = "{" ( __ JSONPair ( __ "," __ JSONPair )* )? __ "}"

JSONPair
  = JSONString __ ":" __ JSONValue

JSONValue
  = JSONString / JSONNumber / JSONObject / JSONArray / "true" / "false" / "null"

JSONString
  = '"' JSONChar* '"'

JSONChar
  = [^"\\] /
    "\\" ( ["bfnrt\\/] / "u" HexDigit HexDigit HexDigit HexDigit )

HexDigit
  = [0-9A-Fa-f]

JSONNumber
  = "-" ? ( "0" / [1-9] [0-9]* ) ( "." [0-9]+ )? ( [eE] [+-]? [0-9]+ )?

JSONArray
  = "[" ( __ JSONValue ( __ "," __ JSONValue )* )? __ "]"

ArgumentList
  = head:Argument tail:(__ "," __ Argument)* {
        var result = [head];
        for (var i = 0; i < tail.length; i++) {
            result.push(tail[i][3]);
        }
        return result;
    }

Argument
  = c:( Number / DoubleQuotedArgumentChars / SingleQuotedArgumentChars )

Number = c:[\-.0-9]+ { return c.join(''); }

DoubleQuotedArgumentChars
  = '"' c:DoubleQuotedArgumentChar* '"' { return c.join(''); }

SingleQuotedArgumentChars
  = "'" c:SingleQuotedArgumentChar* "'" { return c.join(''); }

DoubleQuotedArgumentChar 
  = [^"\\] /
    "\\'" { return "'"; } / 
    '\\"' { return '"'; }

SingleQuotedArgumentChar 
  = [^'\\] /
    "\\'" { return "'"; } / 
    '\\"' { return '"'; }

__ = whitespace*

whitespace = [ \t\n\r;]
