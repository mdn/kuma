//@flow
import * as React from 'react';
import { useEffect, useRef } from 'react';

import { getLocale, gettext } from '../l10n.js';
import SearchIcon from '../icons/search.svg';
import CloseIcon from '../icons/close.svg';

type Props = {
    initialQuery: string,
};

export default function Search({ initialQuery }: Props) {
    const locale = getLocale();
    const [showForm, setShowForm] = React.useState(false);
    const [query, setQuery] = React.useState(initialQuery);

    // After our first render, set the input field's initial value
    // and show search form
    const inputfield = useRef(null);
    useEffect(() => {
        if (inputfield.current && query) {
            inputfield.current.value = query;
            setShowForm(true);
        }
    }, [query, showForm]);

    const handleClick = (event) => {
        event.preventDefault();

        if (showForm === true) {
            setShowForm(false);
            setQuery(null);
            if (inputfield.current) {
                inputfield.current.value = '';
            }
        } else {
            setShowForm(true);
            inputfield.current && inputfield.current.focus();
        }
    };

    return (
        <div className={`header-search ${showForm ? 'show-form' : ''}`}>
            <form
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
            <button className="toggle-form" onClick={handleClick}>
                {/* In order for transitions to work correctly we need
                     the `CloseIcon` icon to be in the DOM prior to transitioning.
                    Transitions can also not be done between `display: none` and
                    `display: block` so, we use the `.hide` class which uses
                    `visibility:hidden`
                   */}
                <CloseIcon
                    className={showForm ? 'close-icon' : 'close-icon hide'}
                />

                {/* The `SearchIcon` is not animated and so we can add/remove
                     the SVG dynamically based on the `showForm` state */}
                {!showForm && <SearchIcon className="search-icon" />}

                <span>
                    {showForm
                        ? gettext('Close search')
                        : gettext('Open search')}
                </span>
            </button>
        </div>
    );
}
