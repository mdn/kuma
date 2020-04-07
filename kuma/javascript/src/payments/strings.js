// @flow
import { gettext, interpolate } from '../l10n.js';

export const strings = {
    signup: 'Become a monthly supporter',
    signupDesc:
        'Support MDN with a $5 monthly subscription and get back more of the knowledge and tools you rely on for when your work has to work.',
    thankYou: 'Thank you for becoming a monthly supporter!',
    memberNum: 'You are MDN member number:',
    potentialMemberNum: 'You will be MDN member number:',
};

export const getMemberNumberString = (
    num: ?number,
    isSubscriber?: ?boolean
): ?string => {
    if (isSubscriber && num) {
        return interpolate(gettext('%(text)s %(num)s'), {
            text: strings.memberNum,
            num: num.toLocaleString(),
        });
    }
    if (num) {
        return interpolate(gettext('%(text)s %(num)s'), {
            text: strings.potentialMemberNum,
            num: num.toLocaleString(),
        });
    }
    return null;
};
