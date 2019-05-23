//@flow
import * as React from 'react';
import { useState, useEffect } from 'react';
import { css } from '@emotion/core';
import styled from '@emotion/styled';

const MenuContainer = styled.div`
    // We use relative here not because we need to tweak positioning
    // but because we need to position the menu itself relative to the
    // label position when it is shown.
    position: relative;

    // We need an explicit pointer-events since we set it to none
    // on the entire document when the menu is up, but we need to be
    // able to click on the menu items themselves
    pointer-events: auto;
`;

const MenuLabel = styled.button`
    display: flex;
    flex-direction: row;
    align-items: center;
    white-space: nowrap;
    padding: 0 5px;
    margin: 0 10px;
    border: none;
    :hover {
        background-color: #eee;
    }
    :focus {
        // The default focus outline doesn't look right in Chrome without this
        outline-offset: -3px;
    }
`;

const Arrow = styled.span`
    font-size: 75%;
    padding-left: 2px;
`;

const Menu = styled.ul`
    position: absolute;
    z-index: 100;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    background-color: white;
    border: solid #83d0f2 1.5px;
    box-shadow: 3px 3px 5px rgba(0, 0, 0, 0.25);
    padding: 10px;
    min-width: 100%;
    li {
        padding: 5px;
        white-space: nowrap;
    }
`;

const styles = {
    menuLabelOpen: css({
        backgroundColor: '#83d0f2',
        '&:hover': {
            backgroundColor: '#83d0f2'
        }
    }),

    menuAttachRight: css({ right: 0 }),
    menuClosed: css({ display: 'none' })
};

type DropdownProps = {|
    // The string or component to display. Clicking on this will
    // display the menu
    label: string | React.Node,
    // If set to true, the menu will be anchored to the right edge of
    // the label and may extend beyond the left edge. If this is
    // false or unset, the default behavior is to attach the menu to
    // the left side of the label and allow it to extend beyond the
    // right edge of the label.
    right?: boolean,
    children: React.Node
|};

export default function Dropdown(props: DropdownProps) {
    const [shown, setShown] = useState(false);

    // If the menu is showing, then register capturing event
    // handlers for hiding it and also return a function to
    // deregister those handlers.
    useEffect(() => {
        function handler(e) {
            if (e.type === 'click' || e.key === 'Escape') {
                // We defer the setShown() call to ensure that the link
                // or button in the menu is still visible when the event
                // is dispatched on it. Otherwise the default action
                // (such as form submission) might not happen.
                setTimeout(() => setShown(false));

                // If the browser supports the closest() method and if
                // that method tells us that the event was not inside
                // the menu then just swallow the event and don't let
                // anyone else see it.
                if (
                    e.target &&
                    e.target.closest &&
                    e.target.closest('ul.dropdown-menu') === null
                ) {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                }
            }
        }

        if (shown) {
            window.addEventListener('click', handler, true);
            window.addEventListener('keydown', handler, true);
            if (document.documentElement) {
                // Make the entire document transparent to mouse events
                // so that all events go directly to the html element
                // except for elements (like our menus) that have explictly
                // set pointerEvents to auto. This prevents links in the
                // document from highlighting on hover while a menu is
                // displayed, for example.
                document.documentElement.style.pointerEvents = 'none';
            }
            return () => {
                window.removeEventListener('click', handler, true);
                window.removeEventListener('keydown', handler, true);
                if (document.documentElement) {
                    document.documentElement.style.pointerEvents = 'auto';
                }
            };
        }
    });

    return (
        <MenuContainer>
            <MenuLabel
                css={shown && styles.menuLabelOpen}
                onClick={!shown ? () => setShown(true) : null}
            >
                {props.label}
                <Arrow>{shown ? '▲' : '▼'}</Arrow>
            </MenuLabel>
            <Menu
                className="dropdown-menu"
                css={[
                    props.right && styles.menuAttachRight,
                    !shown && styles.menuClosed
                ]}
            >
                {props.children}
            </Menu>
        </MenuContainer>
    );
}
