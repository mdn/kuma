import * as React from 'react';
import * as Sentry from '@sentry/browser';
import PropTypes from 'prop-types';

import { gettext } from './l10n.js';

if (process.env.SENTRY_DSN) {
    Sentry.init({ dsn: process.env.SENTRY_DSN });
}

export class AppErrorBoundary extends React.Component {
    state = { error: null, eventId: null };

    static getDerivedStateFromError(error) {
        return { error };
    }

    logError = (error, errorInfo) => {
        if (process.env.SENTRY_DSN) {
            Sentry.withScope(scope => {
                scope.setExtras(errorInfo);
                const eventId = Sentry.captureException(error);
                this.setState({ eventId });
            });
        }
    };

    componentDidCatch(error, errorInfo) {
        document.title = 'Application rendering Error';
        this.logError(error, errorInfo);
    }

    render() {
        if (this.state.error) {
            return (
                <ErrorMessage
                    title={gettext('Application rendering error')}
                    eventId={this.state.eventId}
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
    componentDidCatch(error, errorInfo) {
        document.title = 'Content rendering error';
        this.logError(error, errorInfo);
    }
    render() {
        if (this.state.error) {
            return (
                <ErrorMessage
                    title={gettext('Content rendering error')}
                    eventId={this.state.eventId}
                ></ErrorMessage>
            );
        }

        return this.props.children;
    }
}

function ErrorMessage({ title, eventId, children }) {
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

                        {eventId && (
                            <p>
                                <small>
                                    {gettext(
                                        'Error has been successfully reported.'
                                    )}
                                </small>
                            </p>
                        )}
                    </div>
                </section>
            </div>
        </section>
    );
}

ErrorMessage.propTypes = {
    title: PropTypes.string,
    children: PropTypes.element.isRequired,
    eventId: PropTypes.string
};
