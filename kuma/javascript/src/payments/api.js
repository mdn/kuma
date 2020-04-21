import { getCookie } from '../utils.js';

/**
 * API methods for subscriptions
 */
const SUBSCRIPTIONS_URL = '/api/v1/subscriptions/';
const SUBSCRIPTIONS_FEEDBACK_URL = `${SUBSCRIPTIONS_URL}feedback/`;

/**
 * Get all subscriptions
 */
export function getSubscriptions(onSuccess, onError) {
    fetch(SUBSCRIPTIONS_URL)
        .then((res) => {
            if (res.ok) {
                return res.json();
            } else {
                throw new Error(
                    `${res.status} ${res.statusText} fetching ${SUBSCRIPTIONS_URL}`
                );
            }
        })
        .then(
            (data) => onSuccess(data),
            (error) => onError(error)
        );
}

/**
 * Cancel all user subscriptions
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
                    `${res.status} ${res.statusText} deleting ${SUBSCRIPTIONS_URL}`
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
                    `${res.status} ${res.statusText} posting ${SUBSCRIPTIONS_FEEDBACK_URL}`
                );
            }
            return res;
        })
        .then(
            (data) => onSuccess(data),
            (error) => onError(error)
        );
}
