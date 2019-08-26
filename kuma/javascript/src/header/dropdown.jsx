//@flow
import * as React from 'react';

type DropdownProps = {|
    // The string or component to display. Hovering over this will
    // display the menu
    label: string | React.Node,
    // If set to true, the menu will be anchored to the right edge of
    // the label and may extend beyond the left edge. If this is
    // false or unset, the default behavior is to attach the menu to
    // the left side of the label and allow it to extend beyond the
    // right edge of the label.
    right?: boolean,
    // If true, we won't show the arrow next to the menu
    hideArrow?: boolean,
    children: React.Node
|};

export default function Dropdown(props: DropdownProps) {
    return (
        <div className="dropdown-container">
            <button type="button" className="dropdown-menu-label">
                {props.label}
                {!props.hideArrow && (
                    <span className="dropdown-arrow-down">▼</span>
                )}
            </button>
            <ul
                className="dropdown-menu-items"
                style={props.right && { right: 0 }}
            >
                {props.children}
            </ul>
        </div>
    );
}
