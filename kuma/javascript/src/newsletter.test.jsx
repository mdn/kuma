//@flow
import React from 'react';
import { create } from 'react-test-renderer';

import { localize } from './l10n';
import Newsletter from './newsletter.jsx';

describe('Newsletter', () => {
    test('en-US', () => {
        const tree = create(<Newsletter />).toJSON();
        expect(tree).toMatchSnapshot();
    });

    test('de-DE', () => {
        localize('de-DE', {}, null);
        const tree = create(<Newsletter />).toJSON();
        expect(tree).toMatchSnapshot();
    });
});
