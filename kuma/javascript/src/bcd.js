// @flow
import { gettext } from './l10n.js';

/**
 * This file contains functions for working with the BCD tables
 * contained in the HTML of an Article component. The tables are not
 * React elements, so have to add interactivity the old fashioned way
 * and hook it up via useEffect().
 */

// Used by makeRevealButton() below
let revealButtonTemplate = null;

/**
 * Raw BCD tables don't include the UX for showing and hiding
 * implementation notes, so we have to add a button manually. This
 * function creates and returns an HTMLButton element that can be
 * added to table cells.
 */
function makeRevealButton() {
    if (!revealButtonTemplate) {
        revealButtonTemplate = window.document.createElement('div');
        revealButtonTemplate.innerHTML = `<button title="${gettext(
            'Open implementation notes'
        )}" class="bc-history-link only-icon" tabindex="0"><span>${gettext(
            'Open'
        )}</span><i class="ic-history" aria-hidden="true"></i></button>`;
    }
    return revealButtonTemplate.children[0].cloneNode(true);
}

/**
 * When we open or close an implementation note, we animate the bottom
 * border width of the cells above it to make room for it. But there
 * is a different set of cells that need to be animated depending on
 * the screen width. For unknown historical reasons, the screen width
 * is encoded into the zindex of a hidden td element in the thead of
 * the table. This utility function takes a cell as input and returns
 * the set of cells that need to be enlarged to make room for the
 * implementation note. The return value will be an iterable object.
 */
function cellsToEnlarge(cell: HTMLElement) {
    let row = cell.closest('tr');
    if (row) {
        let table = row.closest('table');
        if (table) {
            let td = table.querySelector('thead td');
            if (td) {
                let zindex = window.getComputedStyle(td).zIndex;
                switch (zindex) {
                    case '1':
                        return row.querySelectorAll('td');
                    case '2':
                        return [cell];
                    default:
                        return row.querySelectorAll('th,td');
                }
            }
        }
    }
    return [];
}

/**
 * Open up the implementation note for a BCD table cell
 */
function open(cell: HTMLElement) {
    let row = cell.closest('tr');
    if (!row) {
        return;
    }
    let table = row.closest('table');
    let details = cell.querySelector('.bc-history');
    let button = cell.querySelector('.bc-history-link');

    if (!(table instanceof HTMLElement) || !details || !button) {
        return;
    }
    // Set the new display parameters for the details
    details.style.display = 'block';
    details.style.width = `${table.clientWidth}px`;
    details.style.left = `${table.offsetLeft - cell.offsetLeft}px`;
    details.style.top = `${cell.clientHeight}px`;
    details.setAttribute('aria-hidden', 'false');

    // Measure the height of the details at this new width and position
    let detailsHeight = `${details.clientHeight}px`;

    // But now set the height to 0, so that we can animate it open.
    details.style.height = '0px';

    // In order for the height to actually get set before the animation
    // starts, we need to force a layout by querying the height
    details.clientHeight; // Forces relayout

    // Start animating the height of the details element.
    // TODO: it is never very efficient to animate the height of an element.
    // There ought to be a more efficient way to acheive this effect.
    details.style.transition = 'height 150ms';
    details.style.height = detailsHeight;

    // And make room for the details element by animating the
    // bottom border width of all the cells in the row.
    for (let c of cellsToEnlarge(cell)) {
        c.style.transition = 'border-bottom-width 150ms';
        c.style.borderBottomWidth = detailsHeight;
    }

    // Finlly, mark the cell as active
    cell.classList.add('active');
    cell.setAttribute('aria-expanded', 'true');

    // And flip the icon in the reveal button to indicate that
    // another click will conceal the note
    button.style.transform = 'scale(1, -1)';
}

/**
 * Hide the implementation note for a BCD table cell, optionally
 * animating the close.
 */
function close(cell, animate) {
    let details = cell.querySelector('.bc-history');
    let button = cell.querySelector('.bc-history-link');

    if (!details || !button) {
        return;
    }

    // Animate the border widths back to their default value
    if (animate) {
        for (let c of cellsToEnlarge(cell)) {
            c.style.borderBottomWidth = '';
        }
    }

    function transitionEndHandler() {
        details.removeEventListener('transitionend', transitionEndHandler);
        details.style.display = 'none';
        details.style.height = 'auto';
        details.style.transition = '';
    }

    if (animate) {
        details.style.height = '0px';
        details.addEventListener('transitionend', transitionEndHandler);
    } else {
        // If we're not animating, just do these things from the
        // transition end handler.
        details.style.display = 'none';
        details.style.height = 'auto';
    }

    // Make the cell inactive
    button.style.transform = '';
    details.setAttribute('aria-hidden', 'true');
    cell.classList.remove('active');
    cell.setAttribute('aria-expanded', 'false');
}

/**
 * When a BCD table includes implementation notes, we want to display
 * a little down arrow to reveal the notes. This will be invoked via
 * useEffect() in article.jsx. The implementation here is based on the
 * code in static/js/wiki-compat-tables.js (but has been substantially
 * modified to remove the jQuery dependency). If you fix a bug here
 * you may also want to fix it in that other file.
 */
export function activateBCDTables(root: HTMLElement) {
    // All cells in all tables that have implementation notes need
    // a unique id. This variable lets us generate them.
    let cellNumber = 0;

    // Loop through all BCD tables under the specified element
    const tables = root.querySelectorAll('.bc-table');
    for (const table of tables) {
        // Find the cells in the table that have implementation notes.
        // For historical reasons we call these notes "history"
        const cells = table.querySelectorAll('.bc-has-history');

        // Keep track of which one of these (if any) is open and visible
        let currentlyOpenCell = null;

        // Activate each of these cells
        for (const cell of cells) {
            // Find the element that contains the implementation note
            const details = cell.querySelector('.bc-history');

            if (!details) {
                continue;
            }

            // Set an id on the details for aria purposes
            let cellId = `bc-history-${++cellNumber}`;
            details.id = cellId;

            // Set cell ARIA attributes, including a reference to
            // the details element
            cell.setAttribute('aria-expanded', 'false');
            cell.setAttribute('aria-controls', cellId);

            // Add the open button right before that element
            let button = makeRevealButton();
            let parent = details.parentElement;
            parent && parent.insertBefore(button, details);

            // Keep track of last open or close so we don't allow rapid clicks.
            let lastClick = 0;

            // Add a click event listener on the cell (not just the open
            // button) to open and close the implementation note
            cell.addEventListener('click', (event: MouseEvent) => {
                // But don't open or close this cell more often than
                // twice a second. Otherwise bugs can occur if we try
                // to transition states when animations are still going on.
                let now = Date.now();
                if (lastClick && now - lastClick < 500) {
                    return;
                }
                lastClick = now;

                // Also, if the click was inside an open note, we don't
                // want to close it for that.
                let target = event.target;
                if (
                    !target ||
                    !(target instanceof HTMLElement) ||
                    target.closest('.bc-history')
                ) {
                    event.stopPropagation();
                    return;
                }

                // Give the button the keyboard focus if it doesn't
                // already have it.
                button.focus();

                // If there is already an open implementation note for this
                // table we want to close it.
                if (currentlyOpenCell) {
                    // If we're going to be opening a different cell
                    // on the same row then we don't want a full closing
                    // animation.
                    let animate =
                        currentlyOpenCell === cell ||
                        currentlyOpenCell.closest('tr') !== cell.closest('tr');

                    close(currentlyOpenCell, animate);
                }

                if (cell !== currentlyOpenCell) {
                    // If the click was on something other than the currently
                    // open cell then we want to open the new cell.
                    currentlyOpenCell = cell;
                    open(cell);
                } else {
                    // Otherwise, the user was just closing an open cell
                    // and there is nothing more to do.
                    currentlyOpenCell = null;
                }
            });
        }
    }
}
