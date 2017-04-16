import sqlalchemy.topological as topological
from sqlalchemy.test import TestBase
from sqlalchemy.test.testing import assert_raises, eq_
from sqlalchemy import exc, util


class DependencySortTest(TestBase):

    def assert_sort(self, tuples, allitems=None):
        if allitems is None:
            allitems = self._nodes_from_tuples(tuples)
        else:
            allitems = self._nodes_from_tuples(tuples).union(allitems)
        result = list(topological.sort(tuples, allitems))
        deps = util.defaultdict(set)
        for parent, child in tuples:
            deps[parent].add(child)
        assert len(result)
        for i, node in enumerate(result):
            for n in result[i:]:
                assert node not in deps[n]

    def _nodes_from_tuples(self, tups):
        s = set()
        for tup in tups:
            s.update(tup)
        return s

    def test_sort_one(self):
        rootnode = 'root'
        node2 = 'node2'
        node3 = 'node3'
        node4 = 'node4'
        subnode1 = 'subnode1'
        subnode2 = 'subnode2'
        subnode3 = 'subnode3'
        subnode4 = 'subnode4'
        subsubnode1 = 'subsubnode1'
        tuples = [
            (subnode3, subsubnode1),
            (node2, subnode1),
            (node2, subnode2),
            (rootnode, node2),
            (rootnode, node3),
            (rootnode, node4),
            (node4, subnode3),
            (node4, subnode4),
            ]
        self.assert_sort(tuples)

    def test_sort_two(self):
        node1 = 'node1'
        node2 = 'node2'
        node3 = 'node3'
        node4 = 'node4'
        node5 = 'node5'
        node6 = 'node6'
        node7 = 'node7'
        tuples = [(node1, node2), (node3, node4), (node4, node5),
                  (node5, node6), (node6, node2)]
        self.assert_sort(tuples, [node7])

    def test_sort_three(self):
        node1 = 'keywords'
        node2 = 'itemkeyowrds'
        node3 = 'items'
        node4 = 'hoho'
        tuples = [(node1, node2), (node4, node1), (node1, node3),
                  (node3, node2)]
        self.assert_sort(tuples)

    def test_raise_on_cycle_one(self):
        node1 = 'node1'
        node2 = 'node2'
        node3 = 'node3'
        node4 = 'node4'
        node5 = 'node5'
        tuples = [
            (node4, node5),
            (node5, node4),
            (node1, node2),
            (node2, node3),
            (node3, node1),
            (node4, node1),
            ]
        allitems = self._nodes_from_tuples(tuples)
        assert_raises(exc.CircularDependencyError, list,
                      topological.sort(tuples, allitems))

        # TODO: test find_cycles

    def test_raise_on_cycle_two(self):

        # this condition was arising from ticket:362 and was not treated
        # properly by topological sort

        node1 = 'node1'
        node2 = 'node2'
        node3 = 'node3'
        node4 = 'node4'
        tuples = [(node1, node2), (node3, node1), (node2, node4),
                  (node3, node2), (node2, node3)]
        allitems = self._nodes_from_tuples(tuples)
        assert_raises(exc.CircularDependencyError, list,
                      topological.sort(tuples, allitems))

        # TODO: test find_cycles

    def test_raise_on_cycle_three(self):
        question, issue, providerservice, answer, provider = \
            'Question', 'Issue', 'ProviderService', 'Answer', 'Provider'
        tuples = [
            (question, issue),
            (providerservice, issue),
            (provider, question),
            (question, provider),
            (providerservice, question),
            (provider, providerservice),
            (question, answer),
            (issue, question),
            ]
        allitems = self._nodes_from_tuples(tuples)
        assert_raises(exc.CircularDependencyError, list,
                      topological.sort(tuples, allitems))

        # TODO: test find_cycles

    def test_large_sort(self):
        tuples = [(i, i + 1) for i in range(0, 1500, 2)]
        self.assert_sort(tuples)

    def test_ticket_1380(self):

        # ticket:1380 regression: would raise a KeyError

        tuples = [(id(i), i) for i in range(3)]
        self.assert_sort(tuples)

    def test_find_cycle_one(self):
        node1 = 'node1'
        node2 = 'node2'
        node3 = 'node3'
        node4 = 'node4'
        tuples = [(node1, node2), (node3, node1), (node2, node4),
                  (node3, node2), (node2, node3)]
        eq_(topological.find_cycles(tuples,
            self._nodes_from_tuples(tuples)), set([node1, node2,
            node3]))

    def test_find_multiple_cycles_one(self):
        node1 = 'node1'
        node2 = 'node2'
        node3 = 'node3'
        node4 = 'node4'
        node5 = 'node5'
        node6 = 'node6'
        node7 = 'node7'
        node8 = 'node8'
        node9 = 'node9'
        tuples = [  # cycle 1 cycle 2 cycle 3 cycle 4, but only if cycle
                    # 1 nodes are present
            (node1, node2),
            (node2, node4),
            (node4, node1),
            (node9, node9),
            (node7, node5),
            (node5, node7),
            (node1, node6),
            (node6, node8),
            (node8, node4),
            (node3, node1),
            (node3, node2),
            ]
        allnodes = set([
            node1,
            node2,
            node3,
            node4,
            node5,
            node6,
            node7,
            node8,
            node9,
            ])
        eq_(topological.find_cycles(tuples, allnodes), set([
            'node8',
            'node1',
            'node2',
            'node5',
            'node4',
            'node7',
            'node6',
            'node9',
            ]))

    def test_find_multiple_cycles_two(self):
        node1 = 'node1'
        node2 = 'node2'
        node3 = 'node3'
        node4 = 'node4'
        node5 = 'node5'
        node6 = 'node6'
        tuples = [  # cycle 1 cycle 2
            (node1, node2),
            (node2, node4),
            (node4, node1),
            (node1, node6),
            (node6, node2),
            (node2, node4),
            (node4, node1),
            ]
        allnodes = set([
            node1,
            node2,
            node3,
            node4,
            node5,
            node6,
            ])
        eq_(topological.find_cycles(tuples, allnodes), set(['node1',
            'node2', 'node4']))

    def test_find_multiple_cycles_three(self):
        node1 = 'node1'
        node2 = 'node2'
        node3 = 'node3'
        node4 = 'node4'
        node5 = 'node5'
        node6 = 'node6'
        tuples = [  # cycle 1 cycle 2 cycle3 cycle4
            (node1, node2),
            (node2, node1),
            (node2, node3),
            (node3, node2),
            (node2, node4),
            (node4, node2),
            (node2, node5),
            (node5, node6),
            (node6, node2),
            ]
        allnodes = set([
            node1,
            node2,
            node3,
            node4,
            node5,
            node6,
            ])
        eq_(topological.find_cycles(tuples, allnodes), allnodes)
