//@flow
import * as React from 'react';
import { useState, useEffect } from 'react';
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

const MenuLabel = styled.div`
    font-size: 18px;
    font-weight: bold;
    padding: 5px 10px;
    :hover {
        background-color: #eee;
    }
`;

const Arrow = styled.span`
    font-size: 12px;
    padding-left: 2px;
`;

const Menu = styled.ul`
    position: absolute;
    z-index: 100;
    display: flex;
    flex-direction: column;
    box-sizing: border-box;
    background-color: white;
    border: solid black 1px;
    box-shadow: 3px 3px 5px black;
    padding: 10px;
    min-width: 100%;
    li {
        padding: 5px;
        white-space: nowrap;
    }
`;

type DropdownProps = {
    label: string,
    children: Array<React.Node>
};

export default function Dropdown(props: DropdownProps) {
    const [shown, setShown] = useState(false);

    // If the menu is showing, then register capturing event
    // handlers for hiding it and also return a function to
    // deregister those handlers.
    useEffect(() => {
        function handler(e) {
            if (e.type === 'click' || e.key === 'Escape') {
                setShown(false);
                e.stopImmediatePropagation();
            }
        }

        if (shown) {
            window.addEventListener('click', handler, true);
            window.addEventListener('keydown', handler, true);
            document.documentElement.style.pointerEvents = 'none';
            return () => {
                window.removeEventListener('click', handler, true);
                window.removeEventListener('keydown', handler, true);
                document.documentElement.style.pointerEvents = 'auto';
            };
        }
    });

    return (
        <MenuContainer>
            <MenuLabel onClick={!shown ? () => setShown(true) : null}>
                {props.label}
                <Arrow>{shown ? '▲' : '▼'}</Arrow>
            </MenuLabel>
            {shown && <Menu>{props.children}</Menu>}
        </MenuContainer>
    );
}
