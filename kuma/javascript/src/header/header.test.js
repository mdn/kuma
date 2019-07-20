//@flow
import React from 'react';
import { create } from 'react-test-renderer';

import { fakeDocumentData } from '../document.test.js';
import Header from './header.jsx';

test('Header snapshot', () => {
    const header = create(<Header document={fakeDocumentData} />);
    expect(header.toJSON()).toMatchSnapshot();
});
