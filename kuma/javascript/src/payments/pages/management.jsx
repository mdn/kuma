// @flow
import * as React from 'react';
// import { useContext } from 'react';

import { gettext, Interpolated } from '../../l10n.js';
import Subheader from '../components/subheaders/index.jsx';
import CancelSubscriptionForm from '../components/cancel-subscription-form.jsx';
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
    const [showForm, setShowForm]: [
        boolean,
        (((boolean) => boolean) | boolean) => void
    ] = React.useState<boolean>(false);
    // console.log('data', data);

    const handleClick = (event) => {
        event.preventDefault();
        setShowForm(true);
    };

    const renderContent = () => {
        if (activeSubscriptions) {
            const date = new Date(nextPayment);
            const dateOptions = {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
            };
            const formattedDate = new Intl.DateTimeFormat(
                locale,
                dateOptions
            ).format(date);

            return (
                <>
                    <p>Next payment occurs on {formattedDate}.</p>
                    <div className="active-subscriptions">
                        <table>
                            <thead>
                                <tr>
                                    <th className="amount">
                                        {gettext('Amount')}
                                    </th>
                                    <th className="credit-card">
                                        {gettext('Card Number')}
                                    </th>
                                    <th className="credit-card">
                                        {gettext('Expiry')}
                                    </th>
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
                    </div>
                    <button
                        className="confirm toggle"
                        onClick={handleClick}
                        type="button"
                    >
                        {gettext('Cancel subscription')}
                    </button>
                </>
            );
        }
        return (
            <div className="active-subscriptions">
                <p>
                    <Interpolated
                        id={gettext(
                            'You have no active subscriptions. Why not <signupLink />?'
                        )}
                        signupLink={
                            <a href={`/${locale}/payments`}>
                                {gettext('set one up')}
                            </a>
                        }
                    />
                </p>
            </div>
        );
    };

    return (
        <>
            <Subheader title="Manage monthly subscription" />
            <main
                className="contributions-page manage-subscriptions"
                role="main"
                data-testid="management-page"
            >
                <section>
                    <div className="column-8">
                        <h2>Subscriptions</h2>
                        {renderContent()}
                        {showForm && (
                            <CancelSubscriptionForm setShowForm={setShowForm} />
                        )}
                    </div>
                </section>
            </main>
        </>
    );
};

export default ManagementPage;
