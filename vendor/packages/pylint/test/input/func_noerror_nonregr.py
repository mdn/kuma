# pylint: disable-msg=W0104
"""snippets of codes which have at some point made pylint crash"""

__revision__ = 1

def function1(cbarg = lambda: None):
    """
  File "/usr/lib/python2.4/site-packages/logilab/astng/scoped_nodes.py", line
391, in mularg_class # this method doesn't exist anymore
    i = self.args.args.index(argname)
ValueError: list.index(x): x not in list
    """
    cbarg().x
