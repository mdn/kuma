import React from 'react';
import { create } from 'react-test-renderer';
import Logo from '../../kuma/javascript/src/logo.jsx';

test('Logo snapshot', () => {
    const logo = create(<Logo url="https://developer.mozilla.org" />);
    expect(logo.toJSON()).toMatchSnapshot();
});
