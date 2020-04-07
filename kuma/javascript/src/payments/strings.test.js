import { strings, getMemberNumberString } from './strings.js';

describe('getMemberNumberString()', () => {
    it('returns potential member number string', () => {
        const mockSubscriberNum = 20;
        const expected = `${strings.potentialMemberNum} ${mockSubscriberNum}`;
        expect(getMemberNumberString(mockSubscriberNum)).toEqual(expected);
    });

    it('returns current member number string', () => {
        const mockSubscriberNum = 10;
        const mockIsSubscriber = true;
        const expected = `${strings.memberNum} ${mockSubscriberNum}`;
        expect(
            getMemberNumberString(mockSubscriberNum, mockIsSubscriber)
        ).toEqual(expected);
    });

    it('returns null if no number is provided', () => {
        expect(getMemberNumberString()).toEqual(null);
    });
});
