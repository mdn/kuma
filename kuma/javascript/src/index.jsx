// @flow
import React from 'react';
import ReactDOM from 'react-dom';

import ClientSideNav from './client-side-nav.js';
import CurrentUser from './current-user.jsx';
import Header from './header/header.jsx';

let container = document.getElementById('react-header');
if (container) {
    ReactDOM.render(
        <CurrentUser.Provider>
            <Header />
        </CurrentUser.Provider>,
        container
    );
}

ClientSideNav.init();
