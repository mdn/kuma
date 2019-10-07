import * as React from 'react';
import PropTypes from 'prop-types';

import GAProvider from './ga-provider.jsx';
import { gettext } from './l10n.js';

export class AppErrorBoundary extends React.Component {
    state = { error: null };

    static contextType = GAProvider.context;

    static getDerivedStateFromError(error) {
        return { error };
    }

    logError(boundaryName) {
        // https://developers.google.com/analytics/devguides/collection/analyticsjs/events#event_fields
        this.context('send', {
            hitType: 'event',
            eventCategory: 'errorboundary',
            eventAction: boundaryName,
            eventLabel: document.location.href
        });
    }

    componentDidCatch() {
        document.title = 'Application rendering Error';
        this.logError('application');
    }

    render() {
        if (this.state.error) {
            return (
                <ErrorMessage
                    title={gettext('Application rendering error')}
                ></ErrorMessage>
            );
        }

        return this.props.children;
    }
}

AppErrorBoundary.propTypes = {
    children: PropTypes.element.isRequired
};

export class ContentErrorBoundary extends AppErrorBoundary {
    componentDidCatch() {
        document.title = 'Content rendering error';
        this.logError('content');
    }
    render() {
        if (this.state.error) {
            return (
                <ErrorMessage
                    title={gettext('Content rendering error')}
                ></ErrorMessage>
            );
        }

        return this.props.children;
    }
}

function ErrorMessage({ title, children }) {
    return (
        <section id="content">
            <div className="wrap">
                <section id="content-main" className="full" role="main">
                    <div className="content-layout">
                        <h1 className="page-title">{title}</h1>
                        <p>
                            {gettext(
                                'An unhandled error occurred in the application. We apologize for the inconvenience!'
                            )}
                        </p>
                        {children}
                        <p>
                            <button
                                type="button"
                                className="button"
                                onClick={() => document.location.reload(true)}
                            >
                                Reload page
                            </button>
                        </p>
                    </div>
                </section>
            </div>
        </section>
    );
}

ErrorMessage.propTypes = {
    title: PropTypes.string,
    children: PropTypes.element.isRequired
};
