# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.
"""render a tree in HTML.




"""
__docformat__ = "restructuredtext en"


def render_HTML_tree(tree, selected_node=None, render_node=None, caption=None):
    """
    Generate a pure HTML representation of a tree given as an instance
    of a logilab.common.tree.Node

    selected_node is the currently selected node (if any) which will
    have its surrounding <div> have id="selected" (which default
    to a bold border libe with the default CSS).

    render_node is a function that should take a Node content (Node.id)
    as parameter and should return a string (what will be displayed
    in the cell).

    Warning: proper rendering of the generated html code depends on html_tree.css
    """
    tree_depth = tree.depth_down()
    if render_node is None:
        render_node = str

    # helper function that build a matrix from the tree, like:
    # +------+-----------+-----------+
    # | root | child_1_1 | child_2_1 |
    # | root | child_1_1 | child_2_2 |
    # | root | child_1_2 |           |
    # | root | child_1_3 | child_2_3 |
    # | root | child_1_3 | child_2_4 |
    # +------+-----------+-----------+
    # from:
    # root -+- child_1_1 -+- child_2_1
    #       |             |
    #       |             +- child_2_2
    #       +- child_1_2
    #       |
    #       +- child1_3 -+- child_2_3
    #                    |
    #                    +- child_2_2
    def build_matrix(path, matrix):
        if path[-1].is_leaf():
            matrix.append(path[:])
        else:
            for child in path[-1].children:
                build_matrix(path[:] + [child], matrix)

    matrix = []
    build_matrix([tree], matrix)

    # make all lines in the matrix have the same number of columns
    for line in matrix:
        line.extend([None]*(tree_depth-len(line)))
    for i in range(len(matrix)-1, 0, -1):
        prev_line, line = matrix[i-1:i+1]
        for j in range(len(line)):
            if line[j] == prev_line[j]:
                line[j] = None

    # We build the matrix of link types (between 2 cells on a line of the matrix)
    # link types are :
    link_types = {(True,  True,  True ): 1, # T
                  (False, False, True ): 2, # |
                  (False, True,  True ): 3, # + (actually, vert. bar with horiz. bar on the right)
                  (False, True,  False): 4, # L
                  (True,  True,  False): 5, # -
                  }
    links = []
    for i, line in enumerate(matrix):
        links.append([])
        for j in range(tree_depth-1):
            cell_11 = line[j] is not None
            cell_12 = line[j+1] is not None
            cell_21 = line[j+1] is not None and line[j+1].next_sibling() is not None
            link_type = link_types.get((cell_11, cell_12, cell_21), 0)
            if link_type == 0 and i > 0 and links[i-1][j] in (1, 2, 3):
                link_type = 2
            links[-1].append(link_type)


    # We can now generate the HTML code for the <table>
    s = u'<table class="tree">\n'
    if caption:
        s += '<caption>%s</caption>\n' % caption

    for i, link_line in enumerate(links):
        line = matrix[i]

        s += '<tr>'
        for j, link_cell in enumerate(link_line):
            cell = line[j]
            if cell:
                if cell.id == selected_node:
                    s += '<td class="tree_cell" rowspan="2"><div class="selected tree_cell">%s</div></td>' % (render_node(cell.id))
                else:
                    s += '<td class="tree_cell" rowspan="2"><div class="tree_cell">%s</div></td>' % (render_node(cell.id))
            else:
                s += '<td rowspan="2">&nbsp;</td>'
            s += '<td class="tree_cell_%d_1">&nbsp;</td>' % link_cell
            s += '<td class="tree_cell_%d_2">&nbsp;</td>' % link_cell

        cell = line[-1]
        if cell:
            if cell.id == selected_node:
                s += '<td class="tree_cell" rowspan="2"><div class="selected tree_cell">%s</div></td>' % (render_node(cell.id))
            else:
                s += '<td class="tree_cell" rowspan="2"><div class="tree_cell">%s</div></td>' % (render_node(cell.id))
        else:
            s += '<td rowspan="2">&nbsp;</td>'

        s += '</tr>\n'
        if link_line:
            s += '<tr>'
            for j, link_cell in enumerate(link_line):
                s += '<td class="tree_cell_%d_3">&nbsp;</td>' % link_cell
                s += '<td class="tree_cell_%d_4">&nbsp;</td>' % link_cell
            s += '</tr>\n'

    s += '</table>'
    return s
