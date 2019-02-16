// @flow
import * as React from 'react';

const ducksStyle = Object.freeze({
    font: 'bold 26px/29px zillaslab',
    backgroundColor: 'black',
    color: 'white',
    position: 'absolute',
    width: 'calc(219px - 50px)',
    height: '29px',
    top: '15px',
    marginLeft: '50px',
    zIndex: '100',
});

const h2Style = Object.freeze({
    position: 'absolute',
    height: '48px',
    width: '48px',
    lineHeight: '55px',
    left: '11px',
    top: '-5px',
    zIndex: 100,
    backgroundColor: 'black',
    transform: 'scale(-1, 1)',
});

export default ({url} : {|url: string|}) : React.Node => <div>
    <a href={url} className="logo">MDN Web Docs</a>
    <div style={ducksStyle}>ducks&nbsp;</div>
    <h2 style={h2Style}>&#8239;&#x1f986;&#8239;</h2>
</div>;
