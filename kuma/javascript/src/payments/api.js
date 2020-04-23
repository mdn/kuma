import { getCookie } from '../utils.js';

/**
 * API methods for subscriptions
 */
export const SUBSCRIPTIONS_URL = '/api/v1/subscriptions/';
export const SUBSCRIPTIONS_FEEDBACK_URL = `${SUBSCRIPTIONS_URL}feedback/`;

/**
 * Get all user's subscriptions
 *
 * @param {function({ "subscriptions": Array}):void} onSuccess - The callback that handles a successful response.
 * @param {function(string):void} onError - The callback that handles an error.
 */
export function getSubscriptions(onSuccess, onError) {
    fetch(SUBSCRIPTIONS_URL)
        .then((res) => {
            if (res.ok) {
                return res.json();
            } else {
                throw new Error(
                    `${res.status} - ${res.statusText} while fetching ${SUBSCRIPTIONS_URL}`
                );
            }
        })
        .then(
            (data) => onSuccess(data),
            (error) => onError(error)
        );
}

/**
 * Cancel all user's subscriptions
 *
 * @param {function(Object):void} onSuccess - The callback that handles a successful response.
 * @param {function(string):void} onError - The callback that handles an error.
 */
export function deleteSubscriptions(onSuccess, onError) {
    fetch(SUBSCRIPTIONS_URL, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
        .then((res) => {
            if (!res.ok) {
                throw new Error(
                    `${res.status} - ${res.statusText} while deleting ${SUBSCRIPTIONS_URL}`
                );
            }
            return res;
        })
        .then(
            (data) => onSuccess(data),
            (error) => onError(error)
        );
}

/**
 * Submit user feedback to Google Analytics
 *
 * @param {{ "feedback": string }} body - body of request, data type JSON
 * @param {function(Object)} onSuccess - The callback that handles a successful response.
 * @param {function(string)} onError - The callback that handles an error.
 */
export function sendFeedback(body, onSuccess, onError) {
    fetch(SUBSCRIPTIONS_FEEDBACK_URL, {
        method: 'POST',
        body,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
    })
        .then((res) => {
            if (!res.ok) {
                throw new Error(
                    `${res.status} - ${res.statusText} posting ${SUBSCRIPTIONS_FEEDBACK_URL}`
                );
            }
            return res;
        })
        .then(
            (data) => onSuccess(data),
            (error) => onError(error)
        );
}
