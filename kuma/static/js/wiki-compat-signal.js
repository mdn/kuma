(function() {
    'use strict';

    var bcTable;
    var bcSignalBlock;
    var bcSignalCompleteBlock;
    var sendReportButton;
    var nextStepButton;
    var stepsInfoSpan;
    var bcSignalStep;
    var bcSignalSteps = 2;

    /**
     * Toggles main block visibility and resets form completion progress
     */
    function toggleBcSignalBlock () {
        if (bcSignalCompleteBlock.classList.contains('open')) {
            bcSignalCompleteBlock.classList.remove('open');
        } else {
            bcSignalBlock.classList.toggle('open');
        }

        resetControls();
        toStep(1);
    }

    /**
     * Moves user to a step, by settings displaying related blocks
     * @param {Number} step - Step index to be shown
     */
    function toStep (step) {
        if (step !== bcSignalStep) {
            const prevStep = bcSignalStep;
            bcSignalStep = step;
            stepsInfoSpan.innerText = `Step ${bcSignalStep} of ${bcSignalSteps}`;

            document.getElementById(`step-${bcSignalStep}`).classList.add('active');
            if (prevStep) {
                document.getElementById(`step-${prevStep}`).classList.remove('active');
            }
        }
    }

    /**
     * Resets all the controls to initial state
     */
    function resetControls () {
        for (const browser of document.querySelectorAll('.browser.selected')) {
            browser.classList.remove('selected');
        }
        document.getElementById('brief-explanation').value = '';
        document.getElementById('supporting-material').value = '';
        document.getElementById('upload-screenshot').value = '';
        document.querySelector('label[for="upload-screenshot"]').style.display = 'inline-block';
        document.querySelector('.uploaded-screenshot-block').style.display = 'none';
        nextStepButton.classList.add('disabled');
        sendReportButton.classList.add('disabled');
    }

    /**
     * Validates required control inputs and sets corresponding classes to navigation buttons
     */
    function validateControls () {
        const selectRow = document.getElementById('select-row');
        const selectedBrowsersLength = document.querySelectorAll('.browser.selected').length;
        const selectedTableRow = selectRow.options[selectRow.selectedIndex].value;
        const briefExplanation = document.getElementById('brief-explanation').value.trim();

        if (selectedBrowsersLength && selectedTableRow) {
            nextStepButton.classList.remove('disabled');

            if (briefExplanation) {
                sendReportButton.classList.remove('disabled');
            } else {
                sendReportButton.classList.add('disabled');
            }
        } else {
            nextStepButton.classList.add('disabled');
            sendReportButton.classList.add('disabled');
        }
    }

    /**
     * Hides bc signal blocks and returns it to initial state
     */
    function finishReport () {
        // Hide both form block and complete block
        bcSignalBlock.classList.remove('open');
        bcSignalCompleteBlock.classList.remove('open');

        // Go to first step, so if will be shown if the block is opened again
        toStep(1);
        resetControls();
    }

    /**
     * Sends all the data from controls to server, then shows signal complete block
     */
    function sendReport () {
        const browsers = [];
        for (const browser of document.querySelectorAll('.browser.selected > .browser-name')) {
            browsers.push(browser.innerText);
        }

        const selectRow = document.getElementById('select-row');
        const row = selectRow.options[selectRow.selectedIndex].value;
        const briefExplanation = document.getElementById('brief-explanation').value;
        const supportingMaterial = document.getElementById('supporting-material').value;
        const screenshot = document.getElementById('upload-screenshot').files[0];

        const signalApiUrl = '/api/v1/bc-signal';
        const payload = {
            'slug': document.body.dataset.slug,
            'locale': window.location.pathname.split('/')[1],
            // 'browsers': browsers,
            // 'row': row,
            // 'brief_explanation': briefExplanation,
            // 'supporting_material': supportingMaterial,
            // 'screenshot': screenshot
        };

        bcSignalBlock.classList.remove('open');
        bcSignalCompleteBlock.classList.add('open');

        fetch(signalApiUrl, {
            method: 'POST',
            body: JSON.stringify(payload),
            headers: {
                'X-CSRFToken': mdn.utils.getCookie('csrftoken'),
                'Content-Type': 'application/json'
            }
        }).then(function() {
            // signalLink.textContent = 'Thank you for letting us know!';
        }).catch(function() {
            // signalLink.textContent = 'Something went wrong!';
        }).then(function() {
            // setTimeout(function() {
            //     container.classList.add('slideUp');
            // }, 1000);
        });
    }

    /**
     * Builds and creates round label for form control steps
     * @param {Number} number - Number inside label, which is step index
     * @param {Boolean} inline - Boolean defining if label should be inline
     * @returns Step label as a `HTMLElement`
     */
    function createStepNumLabel (number, inline) {
        const stepNumLabel = document.createElement('span');
        let klass = 'step-num';
        if (inline) {
            klass += ' inline';
        }

        stepNumLabel.className = klass;
        stepNumLabel.innerText = number;
        return stepNumLabel;
    }

    /**
     * Builds and wraps element in a form control from given element and parameters from controlObj
     * @param {Object} controlObj - Object containing element that needs to be wrapped and related params
     * @returns Form control as a `HTMLElement`
     */
    function createFormControl (controlObj) {
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
        controlDescription.className = 'control-description';

        controlHeader.appendChild(createStepNumLabel(controlObj.index, true));
        controlHeader.appendChild(document.createTextNode(controlObj.header));
        controlDescription.innerHTML = controlObj.description;

        controlInnerWrapper.appendChild(controlHeader);
        controlInnerWrapper.appendChild(controlDescription);

        if (controlObj.optional) {
            const optional = document.createElement('span');
            optional.className = 'optional-text';
            optional.innerText = 'Optional';
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
    }

    /**
     * Builds and creates browser select control with logos and names parsed from bc table
     * @returns Browser control as a `HTMLElement`
     */
    function createSelectBrowserControl () {
        const headerText = 'Which browsers are affected?';
        const descriptionText = 'Please select the browser or browsers which are affected.';

        const browserControlBlock = document.createElement('div');
        browserControlBlock.className = 'select-browser-block';
        const browsers = document.querySelectorAll('.bc-table th[class^=\'bc-browser-\']');
        for (const elem of browsers) {
            const browserBgStyle = window.getComputedStyle(elem.querySelector('span'), ':before').getPropertyValue('background-image');
            const browserLogoSrc = browserBgStyle.replace('url(','').replace(')','').replace(/"/gi, '');
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

            browserBlock.addEventListener('click', function () {
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
    }

    /**
     * Builds and creates row select control with options parsed from bc table
     * @returns Select row control as a `HTMLElement`
     */
    function createSelectRowControl () {
        const headerText = 'Which table row is affected?';
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
    }

    /**
     * Builds and creates brief explanation control which is basically a textarea
     * @returns Brief explanation control as a `HTMLElement`
     */
    function createBriefExplanationControl () {
        const headerText = 'Can you provide a brief explanation?';
        const descriptionText = 'Briefly outline the issue you are highlighting.';

        const textAreaControl = document.createElement('textarea');
        textAreaControl.className = 'control-input';
        textAreaControl.id = 'brief-explanation';

        textAreaControl.addEventListener('input', function () {
            validateControls();
        });

        return createFormControl({
            header: headerText,
            description: descriptionText,
            el: textAreaControl,
            index: 3
        });
    }

    /**
     * Builds and creates supporting material control which is basically a textarea
     * @returns Supporting material control as a `HTMLElement`
     */
    function createSupportingMaterialControl () {
        const headerText = 'Do you have any supporting material?';
        const descriptionText = `
            <b>Browser documentation and release notes</b> are good supporting items to accompany your message.
            A demo hosted on services like <b>Codepen</b> or <b>JSBin</b> are perfect for providing real examples of
            your findings.
        `;

        const textAreaControl = document.createElement('textarea');
        textAreaControl.className = 'control-input';
        textAreaControl.id = 'supporting-material';

        return createFormControl({
            header: headerText,
            description: descriptionText,
            el: textAreaControl,
            index: 4,
            optional: true
        });
    }

    /**
     * Builds and creates screenshot upload control with event listener
     * @returns Screenshot upload control as a `HTMLElement`
     */
    function createUploadScreenshotControl () {
        const uploadScreenshotBlock = document.createElement('div');
        const uploadedScreenshotBlock = document.createElement('div');
        const headerText = 'Can you provide a screenshot?';

        const inputTypeFileControlLabel = document.createElement('label');
        const inputTypeFileControl = document.createElement('input');
        const screenshotFileName = document.createElement('span');
        const deleteScreenshotButton = document.createElement('button');
        const innerButtonSpan = document.createElement('span');

        inputTypeFileControlLabel.setAttribute('for', 'upload-screenshot');
        inputTypeFileControlLabel.className = 'button neutral';
        uploadedScreenshotBlock.className = 'uploaded-screenshot-block';
        screenshotFileName.className = 'uploaded-filename';
        uploadScreenshotBlock.className = 'upload-screenshot-control';
        deleteScreenshotButton.className = 'button neutral delete-screenshot-btn';
        innerButtonSpan.className = 'icon-remove';
        inputTypeFileControl.setAttribute('type', 'file');
        inputTypeFileControl.id = 'upload-screenshot';
        inputTypeFileControl.style.display = 'none';


        inputTypeFileControl.addEventListener('change', function () {
            const value = this.value;
            const startIndex = (value.indexOf('\\') >= 0 ? value.lastIndexOf('\\') : value.lastIndexOf('/'));
            let filename = value.substring(startIndex);

            if (filename.indexOf('\\') === 0 || filename.indexOf('/') === 0) {
                filename = filename.substring(1);
                inputTypeFileControlLabel.style.display = 'none';
                screenshotFileName.innerText = filename;
                uploadedScreenshotBlock.style.display = 'flex';
            }
        });

        deleteScreenshotButton.addEventListener('click', function () {
            inputTypeFileControl.value = '';
            inputTypeFileControlLabel.style.display = 'inline-block';
            uploadedScreenshotBlock.style.display = 'none';
        });

        inputTypeFileControlLabel.appendChild(inputTypeFileControl);
        inputTypeFileControlLabel.appendChild(document.createTextNode('Upload'));
        deleteScreenshotButton.appendChild(innerButtonSpan);
        uploadedScreenshotBlock.appendChild(screenshotFileName);
        uploadedScreenshotBlock.appendChild(deleteScreenshotButton);
        uploadedScreenshotBlock.style.display = 'none';

        uploadScreenshotBlock.appendChild(inputTypeFileControlLabel);
        uploadScreenshotBlock.appendChild(uploadedScreenshotBlock);

        return createFormControl({
            header: headerText,
            description: '',
            el: uploadScreenshotBlock,
            index: 5,
            inline: true,
            optional: true
        });
    }

    /**
     * Builds and creates left block with image, header and description
     * @returns Left block as a `HTMLElement`
     */
    function createLeftBlock () {
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

        leftBlockHeader.innerText = 'Tell us what’s wrong with this table';
        leftBlockDescription.innerHTML =  `
            Our goal is to provide accurate, real values for all our compatibility data tables. Notifying MDN of
            inaccurate data or supplying new data pushes us further towards our goal of providing
            <b>100% real values</b> to the developer community. <br /><b>Thank you for helping.</b>
        `;

        closeButtonWrapper.appendChild(closeButton);
        leftBlockWrapper.appendChild(closeButtonWrapper);
        leftBlockWrapper.appendChild(leftBlockImage);
        leftBlockWrapper.appendChild(leftBlockHeader);
        leftBlockWrapper.appendChild(leftBlockDescription);

        return leftBlockWrapper;
    }

    /**
     * Builds and wraps both form steps into a block
     * @returns Form control as a `HTMLElement`
     */
    function createFormControlBlock () {
        const formControlBlockWrapper = document.createElement('div');
        const stepsInfo = document.createElement('h3');
        stepsInfoSpan = document.createElement('span');

        formControlBlockWrapper.className = 'column-7 right-block form-control-block';
        stepsInfo.className = 'highlight-spanned';
        stepsInfoSpan.className = 'highlight-span';

        stepsInfo.appendChild(stepsInfoSpan);
        formControlBlockWrapper.appendChild(stepsInfo);

        formControlBlockWrapper.appendChild(signalStepOneBlock());
        formControlBlockWrapper.appendChild(signalStepTwoBlock());

        return formControlBlockWrapper;
    }

    /**
     * Builds and returns form first step with browser select and row select controls
     * @returns Form first step as a `HTMLElement`
     */
    function signalStepOneBlock () {
        const signalStepOneBlock = document.createElement('div');
        const controls = document.createElement('div');
        const stepsButtonBlock = document.createElement('div');
        const nextStepButtonIcon = document.createElement('span');
        nextStepButton = document.createElement('button');

        signalStepOneBlock.className = 'inner-step';
        signalStepOneBlock.id = 'step-1';
        controls.className = 'controls';
        stepsButtonBlock.className = 'navigation-buttons reverse';
        nextStepButton.className = 'button neutral disabled next-step-btn';

        nextStepButton.addEventListener('click', function () {toStep(2);});
        nextStepButton.innerHTML = 'Next step (2 of 2)';
        // nextStepButton.appendChild(document.createTextNode());
        // nextStepButton.appendChild(document.createElement(arrowLeftIcon));

        stepsButtonBlock.appendChild(nextStepButton);
        controls.appendChild(createSelectBrowserControl());
        controls.appendChild(createSelectRowControl());
        signalStepOneBlock.appendChild(controls);
        signalStepOneBlock.appendChild(stepsButtonBlock);

        return signalStepOneBlock;
    }

    /**
     * Builds and returns form second step with brieft description, supporting material and screenshot upload controls
     * @returns Form second step as a `HTMLElement`
     */
    function signalStepTwoBlock() {
        const signalStepTwoBlock = document.createElement('div');
        const controls = document.createElement('div');
        const stepsButtonBlock = document.createElement('div');
        const goBackButton = document.createElement('button');
        sendReportButton = document.createElement('button');

        signalStepTwoBlock.id = 'step-2';
        sendReportButton.className = 'button neutral disabled main-btn';
        sendReportButton.innerText = 'Send report';
        signalStepTwoBlock.className = 'inner-step';
        controls.className = 'controls';
        stepsButtonBlock.className = 'navigation-buttons reverse';
        goBackButton.className = 'button prev-step-btn btn-dark';

        goBackButton.innerHTML = '<span class="icon"></span>Previous step';

        sendReportButton.addEventListener('click', sendReport);
        goBackButton.addEventListener('click', function () {toStep(1);});

        stepsButtonBlock.appendChild(sendReportButton);
        stepsButtonBlock.appendChild(goBackButton);

        controls.appendChild(createBriefExplanationControl());
        controls.appendChild(createSupportingMaterialControl());
        controls.appendChild(createUploadScreenshotControl());

        signalStepTwoBlock.appendChild(controls);
        signalStepTwoBlock.appendChild(stepsButtonBlock);

        return signalStepTwoBlock;
    }

    /**
     * Builds and returns container for bc signal elements
     * @returns Signal container block as a `HTMLElement`
     */
    function signalStepsBlock () {
        bcSignalBlock = document.createElement('div');
        bcSignalBlock.className = 'column-container bc-signal-block';

        bcSignalBlock.appendChild(createLeftBlock());
        bcSignalBlock.appendChild(createFormControlBlock(bcSignalStep));

        return bcSignalBlock;
    }

    /**
     * Builds and returns block which will be shown when user submits report
     * @returns Complete block as a `HTMLElement`
     */
    function signalCompleteBlock () {
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
        bcSignalCompleteBlock.className = 'column-container bc-signal-block complete';
        completeImageTextBlock.className = 'complete-left-block-header';
        completeLeftBlock.className = 'column-half left-block';
        completeRightTextBlock.className = 'right-block-header';
        completeRightBlock.className = 'column-half right-block';
        completeImageBlock.className = 'complete-left-block-image';
        completeRightBlockDescription.className = 'right-block-main-text';
        completeImageBlock.style.display = 'block';
        finishButton.className = 'button neutral main-btn';
        finishButton.innerText = 'Finish';

        finishButton.addEventListener('click', finishReport);
        completeImageTextBlock.innerText = 'Thank you!';
        completeRightTextBlock.innerHTML = '<span>Report sent</span>';
        completeRightBlockDescription.innerHTML = `
            <b>What happens next?</b><br />
            <p>
                Our team will review your report. Once we verify the information you have supplied we will update this
                browser compatability table accordingly.
            </p>
            <b>Can I keep track of my report?</b><br />
            </p>
                You can join the GitHub repository to see updates and commits for this table data:
            </p>
            <p>
                <a href="https://github.com/mdn/browser-compat-data" target="_blank">
                    https://github.com/mdn/browser-compat-data
                    <span class="icon-external-link"></span>
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

        return bcSignalCompleteBlock;
    }

    /**
     * Creates and returns the signal element HTML
     * @returns signal element HTML
     */
    function signalElem() {
        const extContainer = document.createElement('div');
        const separator = document.createElement('hr');
        const container = document.createElement('div');
        const signalLink = document.createElement('a');
        signalLink.textContent = 'What are we missing ?';

        signalLink.addEventListener('click', function() {
            toggleBcSignalBlock();
        });

        container.setAttribute('class', 'signal-link-container');
        extContainer.setAttribute('class', 'signal-link-ext-container');
        container.appendChild(separator);
        container.appendChild(signalLink);
        extContainer.appendChild(container);
        return extContainer;
    }


    console.log(mdnIcons.getIcon('arrow-left'));
    bcTable = document.querySelector('.bc-table');
    bcTable.insertAdjacentElement('afterend', signalElem());
    bcTable.insertAdjacentElement('afterend', signalStepsBlock());
    bcTable.insertAdjacentElement('afterend', signalCompleteBlock());
})();
