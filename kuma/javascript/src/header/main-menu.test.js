//@flow
import React from 'react';
import { create } from 'react-test-renderer';

import { fakeDocumentData } from '../document.test.js';
import MainMenu from './main-menu.jsx';

test('MainMenu snapshot', () => {
    const mainMenu = create(
        <MainMenu document={fakeDocumentData} locale="en-US" />
    );
    expect(mainMenu.toJSON()).toMatchSnapshot();
});
