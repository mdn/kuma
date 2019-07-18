/* matchMedia has not been implemented by JSDom yet so we 
   need this mock in our Jest tests. 
   https://jestjs.io/docs/en/manual-mocks#mocking-methods-which-are-not-implemented-in-jsdom
   For example usage see: kuma/javascript/src/search-results-page.test.js */
window.matchMedia = jest.fn().mockImplementation(query => {
    return {
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn()
    };
});
