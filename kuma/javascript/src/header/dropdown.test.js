//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import Dropdown from './dropdown.jsx';

jest.useFakeTimers();

test('Dropdown closed and open snapshots', () => {
    const dropdown = create(
        <Dropdown label="Test">
            <li>foo</li>
            <li>bar</li>
        </Dropdown>
    );

    let closedTree = dropdown.toJSON();
    let closedString = JSON.stringify(closedTree);

    // Expect the menu to be closed and take a snapshot.
    // Even though the menu is closed, we expect the content to
    // be in the document so web crawlers and screen readers see it
    expect(closedString).toContain('▼');
    expect(closedString).toContain('foo');
    expect(closedString).toContain('bar');
    expect(closedTree).toMatchSnapshot();
});
