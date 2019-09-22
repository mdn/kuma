// @flow
import { gettext, interpolate } from './l10n.js';
import { getCookie } from './utils.js';

import type { UserData } from './user-provider.jsx';

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

export function activateBCDSignals(
    slug: string,
    locale: string,
    userData: ?UserData
) {
    let bcTable;
    let bcSignalBlock;
    let errorMessageWrapper;
    let bcSignalCompleteBlock;
    let sendReportButton;
    let nextStepButton;
    let stepsInfoSpan;
    let bcSignalStep;
    let bcSignalSteps = 2;

    /**
     * Toggles main block visibility and resets form completion progress
     */
    const toggleBcSignalBlock = () => {
        if (bcSignalCompleteBlock.classList.contains('open')) {
            bcSignalCompleteBlock.classList.remove('open');
        } else {
            bcSignalBlock.classList.toggle('open');
        }

        resetControls();
        toStep(1);
    };

    /**
     * Moves user to a step, by settings displaying related blocks
     * @param {Number} step - Step index to be shown
     */
    const toStep = step => {
        if (step !== bcSignalStep) {
            const prevStep = bcSignalStep;
            bcSignalStep = step;
            stepsInfoSpan.innerText = interpolate(
                gettext('Step %(current)s of %(total)s'),
                {
                    current: bcSignalStep,
                    total: bcSignalSteps
                },
                true
            );

            const stepId =
                document && document.getElementById(`step-${bcSignalStep}`);
            if (stepId && stepId.classList) {
                stepId.classList.add('active');
            }

            const prevStepId =
                document && document.getElementById(`step-${prevStep}`);
            if (prevStep && prevStepId && prevStepId.classList) {
                prevStepId.classList.remove('active');
            }
        }
    };

    /**
     * Resets all the controls to initial state
     */
    const resetControls = () => {
        for (const browser of document.querySelectorAll('.browser.selected')) {
            browser.classList.remove('selected');
        }

        const brief = document && document.getElementById('brief-explanation');
        if (brief && brief instanceof HTMLTextAreaElement && brief.value) {
            brief.value = '';
        }
        const material =
            document && document.getElementById('supporting-material');
        if (material && material instanceof HTMLTextAreaElement) {
            material.value = '';
        }

        const errorMessage =
            document && document.querySelector('.error-message');
        if (
            errorMessage &&
            errorMessage instanceof HTMLElement &&
            errorMessage.classList
        ) {
            errorMessage.classList.remove('visible');
        }

        nextStepButton.classList.add('disabled');
        sendReportButton.classList.add('disabled');
    };

    /**
     * Validates required control inputs and sets corresponding classes to navigation buttons
     */
    const validateControls = () => {
        const selectRow = document && document.getElementById('select-row');
        const selectedBrowsersLength = document.querySelectorAll(
            '.browser.selected'
        ).length;
        let selectedTableRow;
        if (
            selectRow &&
            selectRow instanceof HTMLSelectElement &&
            selectRow.options[selectRow.selectedIndex] &&
            selectRow.options[selectRow.selectedIndex] instanceof
                HTMLOptionElement &&
            selectRow.options[selectRow.selectedIndex].value
        ) {
            selectedTableRow = selectRow.options[selectRow.selectedIndex].value;
        }
        const briefExplanation =
            document && document.getElementById('brief-explanation');
        if (
            briefExplanation &&
            briefExplanation instanceof HTMLTextAreaElement &&
            briefExplanation.value &&
            typeof briefExplanation.value === 'string'
        ) {
            briefExplanation.value.trim();
        }

        if (selectedBrowsersLength && selectedTableRow) {
            nextStepButton.classList.remove('disabled');

            if (
                briefExplanation &&
                briefExplanation instanceof HTMLTextAreaElement &&
                briefExplanation.value &&
                typeof briefExplanation.value === 'string' &&
                briefExplanation.value.length > 0
            ) {
                sendReportButton.classList.remove('disabled');
            } else {
                sendReportButton.classList.add('disabled');
            }
        } else {
            nextStepButton.classList.add('disabled');
            sendReportButton.classList.add('disabled');
        }
    };

    /**
     * Hides bc signal blocks and returns it to initial state
     */
    const finishReport = () => {
        // Hide both form block and complete block
        bcSignalBlock.classList.remove('open');
        bcSignalCompleteBlock.classList.remove('open');

        // Go to first step, so if will be shown if the block is opened again
        toStep(1);
        resetControls();
    };

    /**
     * Sends all the data from controls to server, then shows signal complete block
     */
    const sendReport = () => {
        const browsers = [];
        for (const browser of document.querySelectorAll(
            '.browser.selected > .browser-name'
        )) {
            browsers.push(browser.innerText);
        }

        const selectRow = document.getElementById('select-row');

        let feature = '';
        if (
            selectRow &&
            selectRow instanceof HTMLSelectElement &&
            selectRow.options[selectRow.selectedIndex] &&
            selectRow.options[selectRow.selectedIndex] instanceof
                HTMLOptionElement &&
            selectRow.options[selectRow.selectedIndex].value
        ) {
            feature = selectRow.options[selectRow.selectedIndex].value;
        }

        let explanation = '';
        const explanationEl = document.getElementById('brief-explanation');
        if (
            explanationEl instanceof HTMLTextAreaElement &&
            explanationEl.value
        ) {
            explanation = explanationEl.value;
        }

        let supportingMaterial = '';
        const supportingMaterialEl = document.getElementById(
            'supporting-material'
        );
        if (
            supportingMaterialEl instanceof HTMLTextAreaElement &&
            supportingMaterialEl.value
        ) {
            supportingMaterial = supportingMaterialEl.value;
        }

        const signalApiUrl = '/api/v1/bc-signal';
        const payload = {
            slug: slug,
            locale: locale,
            feature: feature,
            explanation: explanation,
            browsers: browsers.join(', '),
            supporting_material: supportingMaterial // eslint-disable-line camelcase
        };

        fetch(signalApiUrl, {
            method: 'POST',
            body: JSON.stringify(payload),
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        })
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Something went wrong');
                }
                return response;
            })
            .then(function() {
                bcSignalBlock.classList.remove('open');
                bcSignalCompleteBlock.classList.add('open');
            })
            .catch(function() {
                errorMessageWrapper.classList.add('visible');
            });
    };

    /**
     * Builds and creates round label for form control steps
     * @param {Number} number - Number inside label, which is step index
     * @param {Boolean} inline - Boolean defining if label should be inline
     * @returns Step label as a `HTMLElement`
     */
    const createStepNumLabel = (number, inline) => {
        const stepNumLabel = document.createElement('span');
        let stepClass = 'step-num';
        if (inline) {
            stepClass += ' inline';
        }

        stepNumLabel.className = stepClass;
        stepNumLabel.innerText = `${number}`;
        return stepNumLabel;
    };

    /**
     * Builds and wraps element in a form control from given element and parameters from controlObj
     * @param {Object} controlObj - Object containing element that needs to be wrapped and related params
     * @returns Form control as a `HTMLElement`
     */
    const createFormControl = controlObj => {
        const control = document.createElement('div');
        const controlInnerWrapper = document.createElement('div');
        const controlHeader = document.createElement('div');
        const controlDescription = document.createElement('div');

        control.className = 'control';
        controlInnerWrapper.className = 'control-wrap';
        controlHeader.className = 'control-header';
        if (controlObj.inline) {
            controlHeader.className += ' has-control';
        }
        if (controlObj.optional) {
            controlHeader.className += ' with-optional-label';
        }

        controlDescription.className = 'control-description';

        controlHeader.appendChild(createStepNumLabel(controlObj.index, true));
        controlHeader.appendChild(document.createTextNode(controlObj.header));
        controlDescription.innerHTML = controlObj.description;

        controlInnerWrapper.appendChild(controlHeader);
        controlInnerWrapper.appendChild(controlDescription);

        if (controlObj.optional && !controlObj.optionalLabelHidden) {
            const optional = document.createElement('span');
            optional.className = 'optional-text';
            optional.innerText = gettext('Optional');
            controlHeader.appendChild(optional);
        }

        if (controlObj.inline) {
            controlHeader.appendChild(controlObj.el);
        } else {
            controlInnerWrapper.appendChild(controlObj.el);
        }

        control.appendChild(createStepNumLabel(controlObj.index));
        control.appendChild(controlInnerWrapper);

        return control;
    };

    /**
     * Builds and creates browser select control with logos and names parsed from bc table
     * @returns Browser control as a `HTMLElement`
     */
    const createSelectBrowserControl = () => {
        const headerText = gettext('Which browsers are affected?');
        const descriptionText = gettext(
            'Please select the browser or browsers which are affected.'
        );

        const browserControlBlock = document.createElement('div');
        browserControlBlock.className = 'select-browser-block';
        const browsers = document.querySelectorAll(
            '.bc-table th[class^="bc-browser-"]'
        );
        for (const elem of browsers) {
            const browserBgStyle = window
                .getComputedStyle(elem.querySelector('span'), ':before')
                .getPropertyValue('background-image');
            const browserLogoSrc = browserBgStyle
                .replace('url(', '')
                .replace(')', '')
                .replace(/"/gi, '');
            const browserName = elem.innerText;
            const browserBlock = document.createElement('div');
            const browserLogoWrapper = document.createElement('div');
            const browserLogo = document.createElement('img');
            const browserSelectedIconWrapper = document.createElement('span');
            const browserNameBlock = document.createElement('div');

            browserBlock.className = 'browser';
            browserSelectedIconWrapper.className = 'browser-selected-icon';
            browserLogoWrapper.className = 'browser-logo';
            browserNameBlock.className = 'browser-name';
            browserNameBlock.innerText = browserName;

            browserLogo.setAttribute('src', browserLogoSrc);
            browserLogo.setAttribute('alt', browserName);

            browserLogoWrapper.appendChild(browserSelectedIconWrapper);
            browserLogoWrapper.appendChild(browserLogo);
            browserBlock.appendChild(browserLogoWrapper);
            browserBlock.appendChild(browserNameBlock);

            browserBlock.addEventListener('click', function() {
                this.classList.toggle('selected');
                validateControls();
            });

            browserControlBlock.appendChild(browserBlock);
        }

        return createFormControl({
            header: headerText,
            description: descriptionText,
            el: browserControlBlock,
            index: 1
        });
    };

    /**
     * Builds and creates row select control with options parsed from bc table
     * @returns Select row control as a `HTMLElement`
     */
    const createSelectRowControl = () => {
        const headerText = gettext('Which table row is affected?');
        const rowControlBlock = document.createElement('span');
        const selectControl = document.createElement('select');

        selectControl.id = 'select-row';
        rowControlBlock.className = 'select-wrapper';

        const rows = document.querySelectorAll('.bc-table th[scope=row]');
        for (const elem of rows) {
            const featureName = elem.innerText;
            const option = document.createElement('option');
            option.innerText = featureName;
            option.setAttribute('value', featureName);
            selectControl.appendChild(option);
        }

        rowControlBlock.appendChild(selectControl);
        return createFormControl({
            header: headerText,
            description: '',
            el: rowControlBlock,
            index: 2,
            inline: true
        });
    };

    /**
     * Builds and creates brief explanation control which is basically a textarea
     * @returns Brief explanation control as a `HTMLElement`
     */
    const createBriefExplanationControl = () => {
        const headerText = gettext('Can you provide a brief explanation?');
        const descriptionText = gettext(
            'Briefly outline the issue you are highlighting.'
        );

        const textAreaControl = document.createElement('textarea');
        textAreaControl.className = 'control-input';
        textAreaControl.id = 'brief-explanation';
        textAreaControl.maxLength = 200;

        textAreaControl.addEventListener('input', () => {
            validateControls();
        });

        return createFormControl({
            header: headerText,
            description: descriptionText,
            el: textAreaControl,
            index: 3,
            optional: true,
            optionalLabelHidden: true
        });
    };

    /**
     * Builds and creates supporting material control which is basically a textarea
     * @returns Supporting material control as a `HTMLElement`
     */
    const createSupportingMaterialControl = () => {
        const headerText = gettext('Do you have any supporting material?');
        const descriptionText = gettext(
            '<b>Browser documentation and release notes</b> are good supporting items to accompany your message. A demo hosted on services like <b>Codepen</b> or <b>JSBin</b> are perfect for providing real examples of your findings.'
        );

        const textAreaControl = document.createElement('textarea');
        textAreaControl.className = 'control-input';
        textAreaControl.id = 'supporting-material';
        textAreaControl.maxLength = 200;

        return createFormControl({
            header: headerText,
            description: descriptionText,
            el: textAreaControl,
            index: 4,
            optional: true
        });
    };

    /**
     * Builds and creates the error message box
     * @returns Error message box as a `HTMLElement`
     */
    const createErrorMessageHandler = () => {
        const errorLabelEl = document.createElement('span');
        errorLabelEl.className = 'error-label';
        errorLabelEl.innerHTML = gettext('Connection error:');

        const errorTextEl = document.createElement('span');
        errorTextEl.innerHTML = gettext(
            'Sorry, we can’t seem to reach the Server. We are working to fix the problem. Please try again later.'
        );

        errorMessageWrapper = document.createElement('div');
        errorMessageWrapper.className = 'warning error-message';

        errorMessageWrapper.appendChild(errorLabelEl);
        errorMessageWrapper.appendChild(errorTextEl);

        return errorMessageWrapper;
    };

    /**
     * Builds and creates left block with image, header and description
     * @returns Left block as a `HTMLElement`
     */
    const createLeftBlock = () => {
        const leftBlockWrapper = document.createElement('div');
        const leftBlockImage = document.createElement('span');
        const leftBlockHeader = document.createElement('h2');
        const leftBlockDescription = document.createElement('p');
        const closeButtonWrapper = document.createElement('div');
        const closeButton = document.createElement('button');

        closeButton.className = 'button close-btn';
        closeButtonWrapper.className = 'close-button-wrapper';
        leftBlockWrapper.className = 'column-5 left-block';
        leftBlockHeader.className = 'left-block-header';
        leftBlockImage.className = 'left-block-image';

        closeButton.addEventListener('click', toggleBcSignalBlock);

        leftBlockHeader.innerText = gettext(
            'Tell us what’s wrong with this table'
        );
        leftBlockDescription.innerHTML = interpolate(
            gettext(
                'Our goal is to provide accurate, real values for all our compatibility data tables. Notifying MDN of inaccurate data or supplying new data pushes us further towards our goal of providing %(bStart)s100% real values%(bEnd)s to the developer community. %(br)s%(bStart)sThank you for helping.%(bEnd)s'
            ),
            {
                bStart: '<b>',
                bEnd: '</b>',
                br: '<br />'
            },
            true
        );

        closeButtonWrapper.appendChild(closeButton);
        leftBlockWrapper.appendChild(closeButtonWrapper);
        leftBlockWrapper.appendChild(leftBlockImage);
        leftBlockWrapper.appendChild(leftBlockHeader);
        leftBlockWrapper.appendChild(leftBlockDescription);

        return leftBlockWrapper;
    };

    /**
     * Builds and wraps both form steps into a block
     * @returns Form control as a `HTMLElement`
     */
    const createFormControlBlock = () => {
        const formControlBlockWrapper = document.createElement('div');
        const stepsInfo = document.createElement('h3');
        stepsInfoSpan = document.createElement('span');

        formControlBlockWrapper.className =
            'column-7 right-block form-control-block';
        stepsInfo.className = 'highlight-spanned';
        stepsInfoSpan.className = 'highlight-span';

        stepsInfo.appendChild(stepsInfoSpan);
        formControlBlockWrapper.appendChild(stepsInfo);

        formControlBlockWrapper.appendChild(signalStepOneBlock());
        formControlBlockWrapper.appendChild(signalStepTwoBlock());

        return formControlBlockWrapper;
    };

    /**
     * Builds and returns form first step with browser select and row select controls
     * @returns Form first step as a `HTMLElement`
     */
    const signalStepOneBlock = () => {
        const signalStepOneBlock = document.createElement('div');
        const controls = document.createElement('div');
        const stepsButtonBlock = document.createElement('div');
        const nextStepButtonIcon = document.createElement('span');
        nextStepButton = document.createElement('button');

        signalStepOneBlock.className = 'inner-step';
        signalStepOneBlock.id = 'step-1';
        controls.className = 'controls';
        stepsButtonBlock.className =
            'navigation-buttons reverse mob-reduced-space';
        nextStepButton.className = 'button neutral disabled next-step-btn';

        nextStepButton.addEventListener('click', () => {
            toStep(2);
        });
        nextStepButton.innerHTML = gettext('Next step (2 of 2)');

        nextStepButtonIcon.className = 'icon-next';
        nextStepButton.appendChild(nextStepButtonIcon);

        stepsButtonBlock.appendChild(nextStepButton);
        controls.appendChild(createSelectBrowserControl());
        controls.appendChild(createSelectRowControl());
        signalStepOneBlock.appendChild(controls);
        signalStepOneBlock.appendChild(stepsButtonBlock);

        return signalStepOneBlock;
    };

    /**
     * Builds and returns form second step with brieft description and supporting material controls
     * @returns Form second step as a `HTMLElement`
     */
    const signalStepTwoBlock = () => {
        const signalStepTwoBlock = document.createElement('div');
        const controls = document.createElement('div');
        const stepsButtonBlock = document.createElement('div');
        const goBackButton = document.createElement('button');
        sendReportButton = document.createElement('button');

        signalStepTwoBlock.id = 'step-2';
        sendReportButton.className =
            'button neutral disabled main-btn scroll-to-signal';
        sendReportButton.innerText = gettext('Send report');
        signalStepTwoBlock.className = 'inner-step';
        controls.className = 'controls';
        stepsButtonBlock.className = 'navigation-buttons reverse';
        goBackButton.className = 'button prev-step-btn btn-dark';

        goBackButton.innerHTML = `<span class="icon-back"></span>${gettext(
            'Previous step'
        )}`;

        sendReportButton.addEventListener('click', sendReport);
        goBackButton.addEventListener('click', () => {
            toStep(1);
        });

        stepsButtonBlock.appendChild(sendReportButton);
        stepsButtonBlock.appendChild(goBackButton);

        controls.appendChild(createBriefExplanationControl());
        controls.appendChild(createSupportingMaterialControl());
        controls.appendChild(createErrorMessageHandler());

        signalStepTwoBlock.appendChild(controls);
        signalStepTwoBlock.appendChild(stepsButtonBlock);

        return signalStepTwoBlock;
    };

    /**
     * Builds and returns container for bc signal elements
     * @returns Signal container block as a `HTMLElement`
     */
    const signalStepsBlock = () => {
        bcSignalBlock = document.createElement('div');
        bcSignalBlock.className = 'column-container bc-signal-block';

        bcSignalBlock.appendChild(createLeftBlock());
        bcSignalBlock.appendChild(createFormControlBlock());

        return bcSignalBlock;
    };

    /**
     * Builds and returns block which will be shown when user submits report
     * @returns Complete block as a `HTMLElement`
     */
    const signalCompleteBlock = () => {
        bcSignalCompleteBlock = document.createElement('div');
        const completeLeftBlock = document.createElement('div');
        const completeRightBlock = document.createElement('div');
        const completeImageBlock = document.createElement('div');
        const navigationButtons = document.createElement('div');
        const completeRightBlockDescription = document.createElement('div');
        const completeImageTextBlock = document.createElement('h2');
        const completeRightTextBlock = document.createElement('h3');
        const finishButton = document.createElement('button');
        const closeButtonWrapper = document.createElement('div');
        const closeButton = document.createElement('button');

        closeButton.className = 'button close-btn';
        navigationButtons.className = 'navigation-buttons';
        closeButtonWrapper.className = 'close-button-wrapper';
        bcSignalCompleteBlock.className =
            'column-container bc-signal-block complete';
        completeImageTextBlock.className = 'complete-left-block-header';
        completeLeftBlock.className = 'column-half left-block';
        completeRightTextBlock.className = 'right-block-header';
        completeRightBlock.className = 'column-half right-block';
        completeImageBlock.className = 'complete-left-block-image';
        completeRightBlockDescription.className = 'right-block-main-text';
        completeImageBlock.style.display = 'block';
        finishButton.className = 'button neutral main-btn';
        finishButton.innerText = gettext('Finish');

        finishButton.addEventListener('click', finishReport);
        completeImageTextBlock.innerText = gettext('Thank you!');
        completeRightTextBlock.innerHTML = `<span>${gettext(
            'Report sent'
        )}</span>`;
        completeRightBlockDescription.innerHTML = `
            <h4>${gettext('What happens next?')}</h4>
            <p>
                ${gettext(
                    'Our team will review your report. Once we verify the information you have supplied we will update this browser compatability table accordingly.'
                )}
            </p>
            <h4>${gettext('Can I keep track of my report?')}</h4>
            <p>
                ${gettext(
                    'You can join the GitHub repository to see updates and commits for this table data'
                )}:
            </p>
            <p>
                <a href="https://github.com/mdn/browser-compat-data" target="_blank" rel="noopener noreferrer">
                    https://github.com/mdn/browser-compat-data
                    <span class="external external-icon"></span>
                </a>
            </p>
        `;

        closeButton.addEventListener('click', toggleBcSignalBlock);

        navigationButtons.appendChild(finishButton);
        closeButtonWrapper.appendChild(closeButton);
        completeLeftBlock.appendChild(closeButtonWrapper);
        completeLeftBlock.appendChild(completeImageBlock);
        completeLeftBlock.appendChild(completeImageTextBlock);
        completeRightBlock.appendChild(completeRightTextBlock);
        completeRightBlock.appendChild(completeRightBlockDescription);
        completeRightBlock.appendChild(navigationButtons);

        bcSignalCompleteBlock.appendChild(completeLeftBlock);
        bcSignalCompleteBlock.appendChild(completeRightBlock);

        const scrollElems = document.querySelectorAll('.scroll-to-signal');
        const scrollTo = bcSignalCompleteBlock;

        for (let i = 0; i < scrollElems.length; i++) {
            const elem = scrollElems[i];

            elem.addEventListener('click', (e /*: MouseEvent*/) => {
                e.preventDefault();
                if (window.innerWidth >= 1024) {
                    return;
                }
                const scrollEndElem = scrollTo;

                requestAnimationFrame(timestamp => {
                    const stamp = timestamp || new Date().getTime();
                    const duration = 100;
                    const start = stamp;

                    const startScrollOffset = window.pageYOffset;
                    const scrollEndElemTop = scrollEndElem.getBoundingClientRect()
                        .top;

                    scrollToElem(
                        start,
                        stamp,
                        duration,
                        scrollEndElemTop,
                        startScrollOffset
                    );
                });
            });
        }

        return bcSignalCompleteBlock;
    };

    /**
     * Scrolls to a specified element
     */
    const scrollToElem = (
        startTime,
        currentTime,
        duration,
        scrollEndElemTop,
        startScrollOffset
    ) => {
        const easeInCubic = t => t * t * t;
        const runtime = currentTime - startTime;
        let progress = runtime / duration;

        progress = Math.min(progress, 1);

        const ease = easeInCubic(progress);

        window.scroll(0, startScrollOffset + scrollEndElemTop * ease);
        if (runtime < duration) {
            requestAnimationFrame(timestamp => {
                const currentTime = timestamp || new Date().getTime();
                scrollToElem(
                    startTime,
                    currentTime,
                    duration,
                    scrollEndElemTop,
                    startScrollOffset
                );
            });
        }
    };

    /**
     * Creates and returns the signal element HTML
     * @returns signal element HTML
     */
    const signalElem = () => {
        const extContainer = document.createElement('div');
        const separator = document.createElement('hr');
        const container = document.createElement('div');
        const signalLink = document.createElement('a');
        signalLink.textContent = gettext('What are we missing?');
        signalLink.setAttribute('class', 'scroll-to-signal');
        signalLink.href = '#';

        signalLink.addEventListener('click', function() {
            toggleBcSignalBlock();
        });

        container.setAttribute('class', 'signal-link-container');
        extContainer.setAttribute('class', 'signal-link-ext-container');
        container.appendChild(separator);
        container.appendChild(signalLink);
        extContainer.appendChild(container);
        return extContainer;
    };

    bcTable = document && document.querySelector('.bc-table');
    const waffleEnabled = userData && userData.waffle.flags['bc-signals'];

    if (waffleEnabled && bcTable && bcTable.insertAdjacentElement) {
        bcTable.insertAdjacentElement('afterend', signalElem());
        bcTable.insertAdjacentElement('afterend', signalStepsBlock());
        bcTable.insertAdjacentElement('afterend', signalCompleteBlock());
    }
}
