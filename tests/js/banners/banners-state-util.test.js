const bannersStateUtils = require('../../../kuma/static/js/components/cta-banner/utils/banners-state-util.js');

describe('setBannerActive', function() {
    it('throws and error if banner property is not set', function() {
        function setBannerStateWithoutProp() {
            bannersStateUtils.setBannerActive();
        }
        expect(setBannerStateWithoutProp).toThrow(
            'setBannerActive: The banner property is required'
        );
    });
});
