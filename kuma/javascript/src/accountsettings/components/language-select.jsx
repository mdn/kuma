// @flow
import * as React from 'react';

type Props = {
    defaultValue?: string,
    label: string,
    name: string,
    sortedLanguages: Object,
};

function getLanguageSelectorOptions(sortedLanguages) {
    let options = [];

    for (let language in sortedLanguages) {
        options.push(
            <option key={language} value={language}>
                {sortedLanguages[language]}
            </option>
        );
    }
    return options;
}

const LanguageSelect = ({
    defaultValue = 'en-US',
    label,
    name,
    sortedLanguages,
}: Props) => {
    return (
        <>
            <label htmlFor={name}>{label}</label>
            <select id={name} name={name} defaultValue={defaultValue}>
                {getLanguageSelectorOptions(sortedLanguages)}
            </select>
        </>
    );
};

export default LanguageSelect;
