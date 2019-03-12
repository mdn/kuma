//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import Header from './header.jsx';

test('Header snapshot', () => {
    const header = create(<Header />);
    expect(header.toJSON()).toMatchSnapshot();
});
