import React from 'react';
import { create } from 'react-test-renderer';
import Logo from './logo.jsx';

test('Logo snapshot', () => {
    const logo = create(<Logo url="https://developer.mozilla.org" />);
    expect(logo.toJSON()).toMatchSnapshot();
});
