import * as React from 'react';
import PropTypes from 'prop-types';

import { gettext } from './l10n.js';

export class AppErrorBoundary extends React.Component {
    state = { error: null };

    static getDerivedStateFromError(error) {
        return { error };
    }

    logError() {
        // https://github.com/mozilla/kuma/issues/5833
        // When we start to use Sentry, change the method signature to
        // logError(error, errorInfo) {
    }

    componentDidCatch(error, errorInfo) {
        document.title = 'Application rendering Error';
        this.logError(error, errorInfo);
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
    componentDidCatch(error, errorInfo) {
        document.title = 'Content rendering error';
        this.logError(error, errorInfo);
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
                                'An unhandled error occurred in the application. The error has been logged and an administrator was notified. We apologize for the inconvenience!'
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
