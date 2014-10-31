from pyparsing import *

testdata = """
  int func1(float *arr, int len, double arg1);
  int func2(float **arr, float *arr2, int len, double arg1, double arg2);
  """
  
ident = Word(alphas, alphanums + "_")
vartype = Combine( oneOf("float double int char") + Optional(Word("*")), adjacent = False)
arglist = delimitedList( Group(vartype.setResultsName("type") + 
                                ident.setResultsName("name")) )
functionCall = Literal("int") + ident.setResultsName("name") + \
                    "(" + arglist.setResultsName("args") + ")" + ";"
                    
for fn,s,e in functionCall.scanString(testdata):
    print fn.name
    for a in fn.args:
        print " -",a.type, a.name