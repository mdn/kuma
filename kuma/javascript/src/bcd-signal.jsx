// @flow
import { gettext, interpolate } from './l10n.js';
import { getCookie } from './utils.js';

let bcSignalsInvoked = false;

window.activateBCDSignals = (slug: string, locale: string) => {
    if (bcSignalsInvoked) {
        return;
    }
    // Set control to true to avoid multiple calls on component rerender
    bcSignalsInvoked = true;

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
                }
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
                briefExplanation.value.trim().length > 0
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
                    throw new Error(
                        `Response was not OK (${response.statusText})`
                    );
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
            controlHeader.classList.add('has-control');
        }
        if (controlObj.optional) {
            controlHeader.classList.add('with-optional-label');
        }

        controlDescription.className = 'control-description';

        controlHeader.appendChild(createStepNumLabel(controlObj.index, true));
        controlHeader.appendChild(document.createTextNode(controlObj.header));
        controlDescription.innerText = controlObj.description;

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
            browserLogo.setAttribute('role', 'img');
            browserLogo.setAttribute('aria-hidden', 'true');

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
        textAreaControl.maxLength = 1000;

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

        // If we could use markup in the localized strings I would ideally say
        // '<b>Browser documentation and release notes</b> are good supporting items to accompany your message. A demo hosted on services like <b>Codepen</b> or <b>JSBin</b> are perfect for providing real examples of your findings.'
        // See https://github.com/mozilla/kuma/issues/5886
        const descriptionText = gettext(
            'Browser documentation and release notes are good supporting items to accompany your message. A demo hosted on services like Codepen or JSBin are perfect for providing real examples of your findings.'
        );

        const textAreaControl = document.createElement('textarea');
        textAreaControl.className = 'control-input';
        textAreaControl.id = 'supporting-material';
        textAreaControl.maxLength = 1000;

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
        errorLabelEl.innerText = gettext('Connection error:');

        const errorTextEl = document.createElement('span');
        errorTextEl.innerText = gettext(
            'Sorry, we can’t seem to reach the server. We are working to fix the problem. Please try again later.'
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
        const lineBreak = document.createElement('br');
        const leftBlockSecondLine = document.createTextNode('');

        closeButton.className = 'button close-btn';
        closeButtonWrapper.className = 'close-button-wrapper';
        leftBlockWrapper.className = 'column-5 left-block';
        leftBlockHeader.className = 'left-block-header';
        leftBlockImage.className = 'left-block-image';

        closeButton.addEventListener('click', toggleBcSignalBlock);

        leftBlockHeader.innerText = gettext(
            'Tell us what’s wrong with this table'
        );

        // Message with markup:
        // 'Our goal is to provide accurate, real values for all our compatibility data tables. Notifying MDN of inaccurate data or supplying new data pushes us further towards our goal of providing <b>100% real values</b> to the developer community. <br><b>Thank you for helping.</b>'
        // See https://github.com/mozilla/kuma/issues/5886
        leftBlockDescription.innerText = gettext(
            'Our goal is to provide accurate, real values for all our compatibility data tables. Notifying MDN of inaccurate data or supplying new data pushes us further towards our goal of providing 100% real values to the developer community.'
        );
        leftBlockSecondLine.nodeValue = gettext('Thank you for helping.');
        leftBlockDescription.appendChild(lineBreak);
        leftBlockDescription.appendChild(leftBlockSecondLine);

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
        nextStepButton.innerText = gettext('Next step (2 of 2)');

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
        const goBackIcon = document.createElement('span');
        sendReportButton = document.createElement('button');

        signalStepTwoBlock.id = 'step-2';
        sendReportButton.className =
            'button neutral disabled main-btn scroll-to-signal';
        sendReportButton.innerText = gettext('Send report');
        signalStepTwoBlock.className = 'inner-step';
        controls.className = 'controls';
        stepsButtonBlock.className = 'navigation-buttons reverse';
        goBackButton.className = 'button prev-step-btn btn-dark';
        goBackIcon.className = 'icon-back';
        const backBtnLabel = document.createTextNode(gettext('Previous step'));

        goBackButton.appendChild(goBackIcon);
        goBackButton.appendChild(backBtnLabel);

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
        const completeRightBlockInner = document.createElement('span');
        const finishButton = document.createElement('button');
        const closeButtonWrapper = document.createElement('div');
        const closeButton = document.createElement('button');
        const rightBlockFirstTitle = document.createElement('h4');
        const rightBlockFirstDescription = document.createElement('p');
        const rightBlockSecondTitle = document.createElement('h4');
        const rightBlockSecondDescription = document.createElement('p');
        const linksBlock = document.createElement('p');
        const linkIcon = document.createElement('span');
        const githubLink = document.createElement('a');

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
        completeRightBlockInner.innerText = gettext('Report sent');

        linkIcon.setAttribute('class', 'external external-icon');
        githubLink.textContent = gettext(
            'https://github.com/mdn/browser-compat-data '
        );
        githubLink.href = 'https://github.com/mdn/browser-compat-data';

        rightBlockFirstTitle.innerText = gettext('What happens next?');
        rightBlockFirstDescription.innerText = gettext(
            'Our team will review your report. Once we verify the information you have supplied we will update this browser compatability table accordingly.'
        );
        rightBlockSecondTitle.innerText = gettext(
            'Can I keep track of my report?'
        );
        rightBlockSecondDescription.innerText = gettext(
            'You can join the GitHub repository to see updates and commits for this table data:'
        );

        closeButton.addEventListener('click', toggleBcSignalBlock);

        navigationButtons.appendChild(finishButton);
        closeButtonWrapper.appendChild(closeButton);
        completeLeftBlock.appendChild(closeButtonWrapper);
        completeLeftBlock.appendChild(completeImageBlock);
        completeLeftBlock.appendChild(completeImageTextBlock);
        githubLink.appendChild(linkIcon);
        linksBlock.appendChild(githubLink);
        completeRightTextBlock.appendChild(completeRightBlockInner);
        completeRightBlockDescription.appendChild(rightBlockFirstTitle);
        completeRightBlockDescription.appendChild(rightBlockFirstDescription);
        completeRightBlockDescription.appendChild(rightBlockSecondTitle);
        completeRightBlockDescription.appendChild(rightBlockSecondDescription);
        completeRightBlockDescription.appendChild(linksBlock);
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

    if (bcTable && bcTable.insertAdjacentElement) {
        bcTable.insertAdjacentElement('afterend', signalElem());
        bcTable.insertAdjacentElement('afterend', signalStepsBlock());
        bcTable.insertAdjacentElement('afterend', signalCompleteBlock());
    }
};
