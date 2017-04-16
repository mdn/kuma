# sexpParser.py
#
# Demonstration of the pyparsing module, implementing a simple S-expression
# parser.
#
# Copyright 2007, by Paul McGuire
#
"""
BNF reference: http://theory.lcs.mit.edu/~rivest/sexp.txt

<sexp>    	:: <string> | <list>
<string>   	:: <display>? <simple-string> ;
<simple-string>	:: <raw> | <token> | <base-64> | <hexadecimal> | 
		           <quoted-string> ;
<display>  	:: "[" <simple-string> "]" ;
<raw>      	:: <decimal> ":" <bytes> ;
<decimal>  	:: <decimal-digit>+ ;
		-- decimal numbers should have no unnecessary leading zeros
<bytes> 	-- any string of bytes, of the indicated length
<token>    	:: <tokenchar>+ ;
<base-64>  	:: <decimal>? "|" ( <base-64-char> | <whitespace> )* "|" ;
<hexadecimal>   :: "#" ( <hex-digit> | <white-space> )* "#" ;
<quoted-string> :: <decimal>? <quoted-string-body>  
<quoted-string-body> :: "\"" <bytes> "\""
<list>     	:: "(" ( <sexp> | <whitespace> )* ")" ;
<whitespace> 	:: <whitespace-char>* ;
<token-char>  	:: <alpha> | <decimal-digit> | <simple-punc> ;
<alpha>       	:: <upper-case> | <lower-case> | <digit> ;
<lower-case>  	:: "a" | ... | "z" ;
<upper-case>  	:: "A" | ... | "Z" ;
<decimal-digit> :: "0" | ... | "9" ;
<hex-digit>     :: <decimal-digit> | "A" | ... | "F" | "a" | ... | "f" ;
<simple-punc> 	:: "-" | "." | "/" | "_" | ":" | "*" | "+" | "=" ;
<whitespace-char> :: " " | "\t" | "\r" | "\n" ;
<base-64-char> 	:: <alpha> | <decimal-digit> | "+" | "/" | "=" ;
<null>        	:: "" ;
"""

from pyparsing import *
from base64 import b64decode
import pprint

def verifyLen(t):
    t = t[0]
    if t.len is not None:
        t1len = len(t[1])
        if t1len != t.len:
            raise ParseFatalException, \
                    "invalid data of length %d, expected %s" % (t1len, t.len)
    return t[1]

# define punctuation literals
LPAR, RPAR, LBRK, RBRK, LBRC, RBRC, VBAR = map(Suppress, "()[]{}|")

decimal = Word("123456789",nums).setParseAction(lambda t: int(t[0]))
bytes = Word(printables)
raw = Group(decimal.setResultsName("len") + Suppress(":") + bytes).setParseAction(verifyLen)
token = Word(alphanums + "-./_:*+=")
base64_ = Group(Optional(decimal,default=None).setResultsName("len") + VBAR 
    + OneOrMore(Word( alphanums +"+/=" )).setParseAction(lambda t: b64decode("".join(t)))
    + VBAR).setParseAction(verifyLen)
    
hexadecimal = ("#" + OneOrMore(Word(hexnums)) + "#")\
                .setParseAction(lambda t: int("".join(t[1:-1]),16))
qString = Group(Optional(decimal,default=None).setResultsName("len") + 
                        dblQuotedString.setParseAction(removeQuotes)).setParseAction(verifyLen)
simpleString = raw | token | base64_ | hexadecimal | qString

# extended definitions
real = Regex(r"[+-]?\d+\.\d*([eE][+-]?\d+)?").setParseAction(lambda tokens: float(tokens[0]))
token = Word(alphanums + "-./_:*+=!<>")

simpleString = real | decimal | raw | token | base64_ | hexadecimal | qString

display = LBRK + simpleString + RBRK
string_ = Optional(display) + simpleString

sexp = Forward()
sexpList = Group(LPAR + ZeroOrMore(sexp) + RPAR)
sexp << ( string_ | sexpList )
    
######### Test data ###########
test00 = """(snicker "abc" (#03# |YWJj|))"""
test01 = """(certificate
 (issuer
  (name
   (public-key
    rsa-with-md5
    (e |NFGq/E3wh9f4rJIQVXhS|)
    (n |d738/4ghP9rFZ0gAIYZ5q9y6iskDJwASi5rEQpEQq8ZyMZeIZzIAR2I5iGE=|))
   aid-committee))
 (subject
  (ref
   (public-key
    rsa-with-md5
    (e |NFGq/E3wh9f4rJIQVXhS|)
    (n |d738/4ghP9rFZ0gAIYZ5q9y6iskDJwASi5rEQpEQq8ZyMZeIZzIAR2I5iGE=|))
   tom
   mother))
 (not-before "1997-01-01_09:00:00")
 (not-after "1998-01-01_09:00:00")
 (tag
  (spend (account "12345678") (* numeric range "1" "1000"))))
"""
test02 = """(lambda (x) (* x x))"""
test03 = """(def length
   (lambda (x)
      (cond
         ((not x) 0)
         (   t   (+ 1 (length (cdr x))))
      )
   )
)
"""
test04 = """(2:XX "abc" (#30# |YWJj|))"""
test05 = """(if (is (window_name) "XMMS") (set_workspace 2))"""
test06 = """(if
  (and
    (is (application_name) "Firefox")
    (or
      (contains (window_name) "Enter name of file to save to")
      (contains (window_name) "Save As")
      (contains (window_name) "Save Image")
    )
  )
  (geometry "+140+122")
)
"""
test07 = """(defun factorial (x)
   (if (zerop x) 1
       (* x (factorial (- x 1)))))
       """
test51 = """(3:XX "abc" (#30# |YWJj|))"""

test52 =     """ 
    (and 
      (or (> uid 1000) 
          (!= gid 20) 
      ) 
      (> quota 5.0e+03) 
    ) 
    """ 

# Run tests
t = None
alltests = [ locals()[t] for t in sorted(locals()) if t.startswith("test") ]

for t in alltests:
    print '-'*50
    print t
    try:
        sexpr = sexp.parseString(t)
        pprint.pprint(sexpr.asList())
    except ParseFatalException, pfe:
        print "Error:", pfe.msg
        print line(pfe.loc,t)
        print pfe.markInputline()
    print
