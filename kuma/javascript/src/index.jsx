// @flow
import React from 'react';
import ReactDOM from 'react-dom';
import Logo from './logo.jsx';

let container = document.getElementById('main-header-logo');
if (container) {
    ReactDOM.render(<Logo url={container.dataset.url} />, container);
}
