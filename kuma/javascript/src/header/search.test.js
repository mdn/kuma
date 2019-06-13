//@flow
import React from 'react';
import { create } from 'react-test-renderer';
import Search from './search.jsx';

test('Search snapshot', () => {
    const search = create(<Search initialQuery="" />);
    expect(search.toJSON()).toMatchSnapshot();
});
