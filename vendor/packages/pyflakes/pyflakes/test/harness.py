
import textwrap, compiler

from twisted.trial import unittest

from pyflakes import checker


class Test(unittest.TestCase):

    def flakes(self, input, *expectedOutputs, **kw):
        w = checker.Checker(compiler.parse(textwrap.dedent(input)), **kw)
        outputs = [type(o) for o in w.messages]
        expectedOutputs = list(expectedOutputs)
        outputs.sort()
        expectedOutputs.sort()
        self.assert_(outputs == expectedOutputs, '''\
for input:
%s
expected outputs:
%s
but got:
%s''' % (input, repr(expectedOutputs), '\n'.join([str(o) for o in w.messages])))
        return w
