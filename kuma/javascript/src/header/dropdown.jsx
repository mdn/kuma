//@flow
import * as React from 'react';
import { useContext } from 'react';

import GAProvider from '../ga-provider.jsx';

type DropdownProps = {|
    // A string set as the id attribute to uniquely identify this
    // Dropdown component
    id?: string,
    // The string or component to display. Hovering over this will
    // display the menu
    label: string | React.Node,
    // An optional string that, when specified, is set as the `id` attribute
    // of the `ul` menu element. This is then also used as the value of the
    // `aria-owns` property on the menu trigger button
    ariaOwns?: string,
    // An optional string that, when spcecified, is used to set a custom
    // label for the menu trigger button using `aria-label`
    ariaLabel?: string,
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
    const ga = useContext(GAProvider.context);

    /**
     * Send a signal to GA when there is an interaction on one
     * of the dropdown menus. For example the language selector
     * in the header section of documentation pages.
     * @param {Object} event - The event object that was triggered
     */
    function sendDropdownInteraction(event) {
        const action = event.target.id;

        ga('send', {
            hitType: 'event',
            eventCategory: 'MozMenu',
            eventAction: action
        });
    }

    return (
        <div className="dropdown-container">
            <button
                id={props.id}
                type="button"
                className="dropdown-menu-label"
                aria-haspopup="true"
                aria-owns={props.ariaOwns}
                aria-label={props.ariaLabel}
                onMouseOver={sendDropdownInteraction}
                onFocus={sendDropdownInteraction}
            >
                {props.label}
                {!props.hideArrow && (
                    <span className="dropdown-arrow-down" aria-hidden="true">
                        ▼
                    </span>
                )}
            </button>
            <ul
                id={props.ariaOwns}
                className={`dropdown-menu-items${props.right ? ' right' : ''}`}
                role="menu"
            >
                {props.children}
            </ul>
        </div>
    );
}
