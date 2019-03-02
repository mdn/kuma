// @flow
import React from 'react';
import ReactDOM from 'react-dom';
import Header from './header/header.jsx';
import ClientSideNav from './client-side-nav.js';

let container = document.getElementById('react-header');
if (container) {
    ReactDOM.render(<Header />, container);
}

ClientSideNav.init();
