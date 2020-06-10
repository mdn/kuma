// @flow
import * as React from 'react';

type Props = {
    defaultValue?: string,
    label: string,
    name: string,
    sortedLanguages: Object,
};

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
                {Object.keys(sortedLanguages).map((language) => (
                    <option key={language} value={language}>
                        {sortedLanguages[language]}
                    </option>
                ))}
            </select>
        </>
    );
};

export default LanguageSelect;
