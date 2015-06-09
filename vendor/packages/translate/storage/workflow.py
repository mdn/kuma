#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""
A workflow is defined by a set of states that a translation unit can be in and
the (allowed) transitions between these states. A state is defined by a range
between -128 and 127, indicating its level of "completeness". The range is
closed at the beginning and open at the end. That is, if a workflow contains
states A, B and C where A < B < C, a unit with state number n is in state A if
A <= n < B, state B if B <= n < C or state C if C <= n < MAX.

A value of 0 is typically the "empty" or "new" state with negative values
reserved for states like "obsolete" or "do not use".

Format specific workflows should be defined in such a way that the numeric
state values correspond to similar states. For example state 0 should be
"untranslated" in PO and "new" or "empty" in XLIFF, state 100 should be
"translated" in PO and "final" in XLIFF. This allows formats to implicitly
define similar states.
"""


class StateEnum:
    """Only contains the constants for default states."""
    MIN = -128
    OBSOLETE = -100
    EMPTY = 0
    NEEDS_WORK = 30
    REJECTED = 60
    NEEDS_REVIEW = 80
    UNREVIEWED = 100
    FINAL = 120
    MAX = 127


class State(object):

    def __init__(self, name, enter_action=None, leave_action=None):
        self.name = name
        self.enter_action = enter_action
        self.leave_action = leave_action

    def __eq__(self, rhs):
        return self.name == rhs.name

    def __repr__(self):
        return '<State "%s">' % (self.name)

    def enter(self, obj):
        if not self.enter_action or not callable(self.enter_action):
            return
        self.enter_action(obj)

    def leave(self, obj):
        if not self.leave_action or not callable(self.leave_action):
            return
        self.leave_action(obj)


class UnitState(State):

    def __init__(self, name, state_value):
        self.state_value = state_value
        super(UnitState, self).__init__(name, self._enter)

    def __repr__(self):
        return '<UnitState name=%s value=%d>' % (self.name, self.state_value)

    def _enter(self, unit):
        unit.set_state_n(self.state_value)


class WorkflowError(Exception):
    pass


class NoInitialStateError(WorkflowError):
    pass


class TransitionError(WorkflowError):
    pass


class InvalidStateObjectError(WorkflowError):

    def __init__(self, obj):
        super(InvalidStateObjectError, self).__init__('Invalid state object: %s' % (obj))


class StateNotInWorkflowError(Exception):

    def __init__(self, state):
        super(StateNotInWorkflowError, self).__init__(
            'State not in workflow: %s' % (state))


class Workflow(object):

    # INITIALISERS #
    def __init__(self, wf_obj=None):
        self._current_state = None
        self._edges = []
        self._initial_state = None
        self._states = []
        self._workflow_obj = wf_obj

    # ACCESSORS #
    def _get_edges(self):
        return list(self._edges)
    edges = property(_get_edges)

    def _get_states(self):
        return list(self._states)
    states = property(_get_states)

    # METHODS #
    def add_edge(self, from_state, to_state):
        if isinstance(from_state, basestring):
            from_state = self.get_state_by_name(from_state)
        if isinstance(to_state, basestring):
            to_state = self.get_state_by_name(to_state)
        for s in (from_state, to_state):
            if s not in self.states:
                raise StateNotInWorkflowError(s)
        if (from_state, to_state) in self.edges:
            return  # Edge already exists. Return quietly

        self._edges.append((from_state, to_state))

    def add_state(self, state):
        if not isinstance(state, State):
            raise InvalidStateObjectError(state)
        if state in self.states:
            raise ValueError('State already in workflow: %s' % (state))
        self._states.append(state)
        if self._initial_state is None:
            self._initial_state = state

    def get_from_states(self):
        """Returns a list of states that can be transitioned from to the
            current state."""
        return [e[0] for e in self.edges if e[1] is self._current_state]

    def get_to_states(self):
        """Returns a list of states that can be transitioned to from the
            current state."""
        return [e[1] for e in self.edges if e[0] is self._current_state]

    def get_state_by_name(self, state_name):
        """Get the ``State`` object for the given name."""
        for s in self.states:
            if s.name == state_name:
                return s
        else:
            raise StateNotInWorkflowError(state_name)

    def set_current_state(self, state):
        """Set the current state. This is absolute and not subject to edge
            constraints. The current state's ``leave`` and the new state's
            ``enter`` method is still called. For edge transitions, see the
            ``trans`` method."""
        if isinstance(state, basestring):
            state = self.get_state_by_name(state)
        if state not in self.states:
            raise StateNotInWorkflowError(state)

        if self._current_state:
            self._current_state.leave(self._workflow_obj)
        self._current_state = state
        self._current_state.enter(self._workflow_obj)

    def set_initial_state(self, state):
        """Sets the initial state, used by the :meth:`.reset` method."""
        if isinstance(state, basestring):
            state = self.get_state_by_name(state)
        if not isinstance(state, State):
            raise InvalidStateObjectError(state)
        if state not in self.states:
            raise StateNotInWorkflowError(state)
        self._initial_state = state

    def reset(self, wf_obj, init_state=None):
        """Reset the work flow to the initial state using the given object."""
        self._workflow_obj = wf_obj
        if init_state is not None:
            if isinstance(init_state, basestring):
                init_state = self.get_state_by_name(init_state)
            if init_state not in self.states:
                raise StateNotInWorkflowError()
            self._initial_state = init_state
            self._current_state = init_state
            return
        if self._initial_state is None:
            raise NoInitialStateError()
        self._current_state = None
        self.set_current_state(self._initial_state)

    def trans(self, to_state=None):
        """Transition to the given state. If no state is given, the first one
            returned by ``get_to_states`` is used."""
        if self._current_state is None:
            raise ValueError('No current state set')
        if isinstance(to_state, basestring):
            to_state = self.get_state_by_name(to_state)
        if to_state is None:
            to_state = self.get_to_states()
            if not to_state:
                raise TransitionError('No state to transition to')
            to_state = to_state[0]
        if to_state not in self.states:
            raise StateNotInWorkflowError(to_state)
        if (self._current_state, to_state) not in self.edges:
            raise TransitionError('No edge between edges %s and %s' % (
                                  self._current_state, to_state))
        self._current_state.leave(self._workflow_obj)
        self._current_state = to_state
        self._current_state.enter(self._workflow_obj)


def create_unit_workflow(unit, state_names):
    wf = Workflow(unit)

    state_info = unit.STATE.items()
    state_info.sort(key=lambda x: x[0])

    init_state, prev_state = None, None
    for state_id, state_range in state_info:
        if state_range[0] < 0:
            continue
        state_name = state_names[state_id]
        # We use the low end value below, because the range is closed there
        state = UnitState(state_name, state_range[0])
        wf.add_state(state)

        # Use the first non-negative state as the initial state...
        if init_state is None and state_range[0] >= 0:
            init_state = state

        if prev_state:
            wf.add_edge(prev_state, state_name)
        prev_state = state_name

    if init_state:
        wf.set_initial_state(init_state)

    return wf
