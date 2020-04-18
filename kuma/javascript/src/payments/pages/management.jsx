// @flow
import * as React from 'react';
// import { useContext } from 'react';

import { gettext, Interpolated } from '../../l10n.js';
import Subheader from '../components/subheaders/index.jsx';
// import UserProvider from '../../user-provider.jsx';

type Props = {
    locale: string,
    data: {
        activeSubscriptions: boolean,
        amount: number,
        last4: string,
        nextPayment: string,
        expires: string,
    },
};

const ManagementPage = ({ data, locale }: Props) => {
    const { activeSubscriptions, amount, last4, nextPayment, expires } = data;
    // console.log('data', data);

    const handleClick = () => {
        // console.log('ev', event);
    };

    const renderContent = () => {
        if (activeSubscriptions) {
            return (
                <>
                    <p>Next payment occurs on {nextPayment}</p>
                    <table className="subscriptions">
                        <thead>
                            <tr>
                                <th>{gettext('Amount')}</th>
                                <th>{gettext('Card Number')}</th>
                                <th>{gettext('Expiry')}</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{`$${amount}`}</td>
                                <td>{`**** **** **** ${last4}`}</td>
                                <td>{expires}</td>
                            </tr>
                            <tr></tr>
                        </tbody>
                    </table>
                    <button
                        className="cancel"
                        onClick={handleClick}
                        type="button"
                    >
                        {gettext('Cancel subscription')}
                    </button>
                </>
            );
        }
        return (
            <p className="subscriptions">
                <Interpolated
                    id={gettext(
                        'You have no active subscriptions. Why not <signupLink />?'
                    )}
                    signupLink={
                        <a href={`${locale}/payments/edit`}>
                            {gettext('set one up')}
                        </a>
                    }
                />
            </p>
        );
    };

    const renderForm = () => {
        return (
            <div className="alert danger">
                <h3>{gettext('Are you sure you want to cancel?')}</h3>
                <p>
                    {gettext(
                        'You will have to set up a new subscription if you wish to resume making payments to MDN Web Docs.'
                    )}
                </p>
                <div className="button-group">
                    <button type="button">
                        {gettext('Keep my membership')}
                    </button>
                    <button type="submit">
                        {gettext('Yes, cancel subscription')}
                    </button>
                </div>
            </div>
        );
    };

    const renderSuccess = () => {
        return (
            <div className="alert success">
                {gettext(
                    'Your monthly subscription has been successfully canceled.'
                )}
            </div>
        );
    };

    const renderError = () => {
        return (
            <div className="alert danger">
                {gettext(
                    'There was a problem canceling your subscription. Please contact <email>'
                )}
            </div>
        );
    };

    return (
        <>
            <Subheader title="Manage monthly subscription" />
            <main
                className="contributions-page"
                role="main"
                data-testid="management-page"
            >
                <section>
                    <div className="column-container">
                        <div className="column-7">
                            <h2>Subscriptions</h2>
                            {renderContent()}
                            {renderForm()}
                            {renderSuccess()}
                            {renderError()}
                        </div>
                    </div>
                </section>
            </main>
        </>
    );
};

export default ManagementPage;
