// @flow
import React from 'react';
import ReactDOM from 'react-dom';
import Header from './header/header.jsx';

let container = document.getElementById('react-header');
if (container) {
    ReactDOM.render(<Header />, container);
}
