/**
 * Helper function to get cookie value given a cookie name
 * @params {string} cookie name
 * @returns {string} cookie value
 */
export function getCookie(name) {
    var cookieValue = null;
    if (document.cookie) {
        var cookies = document.cookie.split(';');
        for (var cookie of cookies) {
            cookie = cookie.trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === name + '=') {
                cookieValue = decodeURIComponent(
                    cookie.substring(name.length + 1)
                );
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Creates a new XMLHttpRequest, sets the specified request
 * headers if specified, and returns the new XMLHttpRequest object
 * @param {String} method - The XMLHttpRequest method to use
 * @param {String} url - The URL endpoint
 * @param {Object} requestHeaders - Request headers as an Object
 *
 * Example requestHeaders
 * -----------------------
 * {
 *   'X-Requested-With': 'XMLHttpRequest',
 *   'Content-type': 'application/x-www-form-urlencoded'
 * }
 *
 * @returns new XMLHttpRequest object
 */
export function initAjaxRequest(method, url, requestHeaders) {
    const xmlHttpRequest = new XMLHttpRequest();
    xmlHttpRequest.open(method, url);

    if (requestHeaders) {
        Object.keys(requestHeaders).forEach(key => {
            xmlHttpRequest.setRequestHeader(key, requestHeaders[key]);
        });
    }

    xmlHttpRequest.timeout = 5000;
    xmlHttpRequest.resposeType = 'json';
    return xmlHttpRequest;
}

/**
 * Given an XMLHttpRequest object, return a Promise that will
 * resolve if the request was successfull, or will be rejected
 * if the `status` is not 200
 * @param {Object} ajaxRequest - The XMLHttpRequest object
 * @returns a new `Promise` object
 */
export function getAjaxResponse(ajaxRequest) {
    return new Promise((resolve, reject) => {
        ajaxRequest.onreadystatechange = () => {
            if (ajaxRequest.readyState === 4) {
                if (
                    ajaxRequest.status === 200 &&
                    ajaxRequest.responseText !== ''
                ) {
                    resolve(ajaxRequest.responseText);
                } else {
                    reject(
                        `Ajax error: ${ajaxRequest.status} : ${ajaxRequest.responseText}`
                    );
                }
            }
        };
    });
}
