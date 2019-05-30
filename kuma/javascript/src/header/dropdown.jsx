//@flow
import * as React from 'react';
import { useRef } from 'react';
import styled from '@emotion/styled';

const MenuContainer = styled.div`
    // We use relative here not because we need to tweak positioning
    // but because we need to position the menu itself relative to the
    // label position when it is shown.
    position: relative;

    // This adjusts for the 5px left padding
    margin-left: -5px;

    :hover {
        & .dropdown-menu-label {
            color: #3d7e9a;
        }
        & .dropdown-menu-label a {
            color: #3d7e9a;
        }
        & .dropdown-menu {
            display: flex;
        }
    }
`;

const MenuLabel = styled.div`
    display: flex;
    flex-direction: row;
    align-items: center;
    white-space: nowrap;
    font-size: 15px;
    font-weight: bold;
    color: #333;
    padding: 0 5px 5px 5px;
    border: none;
    :focus {
        // The default focus outline doesn't look right in Chrome without this
        outline-offset: -3px;
    }
    & a {
        color: #333;
        text-decoration: none;
    }
`;

const Arrow = styled.span`
    font-size: 75%;
    padding-left: 2px;
`;

const Menu = styled.ul`
    position: absolute;
    display: none;
    z-index: 100;
    flex-direction: column;
    box-sizing: border-box;
    background-color: white;
    box-shadow: 0 2px 8px 0 rgba(12, 12, 13, 0.1);
    border: solid 1px #d8dfe2;
    border-radius: 4px;
    padding: 4px 0;
    min-width: 100%;
    & li a,
    & li button {
        display: inline-block;
        box-sizing: border-box;
        width: 100%;
        padding: 6px 16px;
        white-space: nowrap;
        color: #3d7e9a;
        font-size: 15px;
        font-weight: bold;
        /* buttons have centered text by default */
        text-align: start;

        :hover {
            color: #fff;
            background-color: #3d7e9a;
            text-decoration: none;
        }
    }
`;

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

/*
 * This function explicitly hides a menu so that we can exit the CSS
 * :hover state after the user clicks on a link in the menu. Without this
 * the menu would remain visible after a click.
 */
function dismissMenu(menu) {
    if (menu) {
        menu.style.display = 'none';
        setTimeout(() => {
            menu.style.display = null;
        }, 100);
    }
}

export default function Dropdown(props: DropdownProps) {
    let menu = useRef(null);
    return (
        <MenuContainer>
            <MenuLabel className="dropdown-menu-label">
                {props.label}
                {!props.hideArrow && <Arrow>▼</Arrow>}
            </MenuLabel>
            <Menu
                ref={menu}
                onClick={() => dismissMenu(menu.current)}
                className="dropdown-menu"
                style={props.right && { right: 0 }}
            >
                {props.children}
            </Menu>
        </MenuContainer>
    );
}
