// @flow
import * as React from 'react';
import SubHeader from '../components/subheaders/index.jsx';

export const title = 'MDN Web Docs payment terms';
const TermsPage = () => (
    <>
        <SubHeader title={title} />
        <main
            className="contributions-page"
            role="main"
            data-testid="terms-page"
        >
            <section>
                <h2>Payment Terms</h2>

                <p>Mozilla (that’s us) operates MDN Web Docs.</p>
                <p>
                    These Payment Terms cover your payment to MDN.{' '}
                    <a
                        href="https://www.mozilla.org/en-US/about/legal/terms/mozilla/"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        The Websites & Communications Terms of Use
                    </a>{' '}
                    cover the MDN service itself. If there is any inconsistency
                    between these terms and the Websites & Communications Terms
                    of Use, these Payment Terms apply.
                </p>

                <h2>Payment Authorization</h2>
                <p>
                    You can support MDN with a one-time payment, or you can
                    choose to schedule monthly payments. Your payments are not
                    tax deductible.
                </p>
                <p>
                    In order to sign up for monthly payments, you must sign in
                    to MDN using a GitHub account. GitHub has its own{' '}
                    <a
                        href="https://help.github.com/articles/github-terms-of-service/"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Terms
                    </a>{' '}
                    and{' '}
                    <a
                        href="https://help.github.com/articles/github-privacy-statement/"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Privacy Policy
                    </a>
                    .
                </p>
                <p>
                    When you choose to support MDN, you authorize us to charge
                    the payment card you provide for the amount you choose,
                    either as a one-time payment, or as a recurring monthly
                    payment.
                </p>
                <h2>Cancellation</h2>
                <p>
                    If you sign up for monthly payments, you may cancel at any
                    time by sending an email to
                    <a
                        href={`mailto:${contribution_support_email}`}
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        mdn-support@mozilla.com
                    </a>
                    . If you choose to cancel, we will not charge your payment
                    card for subsequent months.
                </p>
                <h2>Privacy Notice</h2>
                <p>
                    Your payment is processed by{' '}
                    <a
                        href="https://stripe.com/us/privacy"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Stripe
                    </a>
                    .
                </p>
                <p>
                    Mozilla receives a record of your payment, information about
                    how much you’ve decided to pay, and whether you’ve set up
                    monthly payments. Mozilla does not receive your payment
                    details. If you sign up for an MDN account, Mozilla also
                    receives the information you include in your account, as
                    well as your email address from your GitHub login. When
                    Mozilla receives information from you, our{' '}
                    <a
                        href="https://www.mozilla.org/en-US/privacy/websites/"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        Mozilla Privacy Policy
                    </a>{' '}
                    describes how we handle that information.
                </p>
            </section>
        </main>
    </>
);

export default TermsPage;
