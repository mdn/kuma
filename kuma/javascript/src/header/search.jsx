//@flow
import * as React from 'react';
import { useEffect, useRef } from 'react';

import { getLocale, gettext } from '../l10n.js';
import SearchIcon from '../icons/search.svg';

type Props = {
    initialQuery: string
};

export default function Search(props: Props) {
    const locale = getLocale();

    // After our first render, set the input field's initial value
    const inputfield = useRef(null);
    useEffect(() => {
        if (inputfield.current && props.initialQuery) {
            inputfield.current.value = props.initialQuery;
        }
    }, [props.initialQuery]);

    return (
        <form
            className="header-search"
            id="nav-main-search"
            action={`/${locale}/search`}
            method="get"
            role="search"
        >
            <SearchIcon className="search-icon" />

            <label htmlFor="main-q" className="visually-hidden">
                {gettext('Search MDN')}
            </label>
            <input
                className="search-input-field"
                ref={inputfield}
                type="search"
                id="main-q"
                name="q"
                placeholder={gettext('Search MDN')}
                pattern="(.|\s)*\S(.|\s)*"
                required
            />
        </form>
    );
}
