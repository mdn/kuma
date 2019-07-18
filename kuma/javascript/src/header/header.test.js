//@flow
import React from 'react';
import { create } from 'react-test-renderer';

// Must be imported before the tested file
import '../__mocks__/matchMedia.js';

import { fakeDocumentData } from '../document.test.js';
import Header from './header.jsx';

test('Header snapshot', () => {
    const header = create(<Header document={fakeDocumentData} />);
    expect(header.toJSON()).toMatchSnapshot();
});
