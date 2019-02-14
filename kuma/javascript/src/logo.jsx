//@flow
import * as React from 'react';

export default function(props : {|url: string|}) : React.Node {
    return (
        <a css={{margin:0}} className="logo" href={props.url}>
          MDN Web Docs
        </a>
    );

    /*
      Or, to get the ducks back:
      <a href="{{ url('home') }}" class="logo">{{ _('MDN Web Docs') }}</a>
      <div style="font: bold 26px/29px zillaslab;
                  background-color:black; color:white;
                  position:relative; left: -50px; height:29px; top:15px;
                  z-index:100">ducks&nbsp;</div>
      <h2 style="position:absolute;height:48px;width:48px;line-height:55px;left:11px;top:-5px;z-index:100;background-color:black;transform:scale(-1,1)">&#8239;&#x1f986;&#8239;</h2>
     */
}
