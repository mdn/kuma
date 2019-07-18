//@flow
import React from 'react';
import { create } from 'react-test-renderer';

// Must be imported before the tested file
import '../__mocks__/matchMedia.js';

import { fakeDocumentData } from '../document.test.js';
import LanguageMenu from './language-menu.jsx';

test('LanguageMenu snapshot', () => {
    const page = create(<LanguageMenu document={fakeDocumentData} />);
    expect(page.toJSON()).toMatchSnapshot();
});
