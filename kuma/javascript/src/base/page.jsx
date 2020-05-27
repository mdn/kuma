// @flow
import * as React from 'react';
import A11yNav from '../a11y/a11y-nav.jsx';
import Header from '../header/header.jsx';
import Footer from '../footer.jsx';

// Common `routes` params shared by page components such as
// `account/pages/index` and `payments/pages/index`
export type PageRoutesParams = {
    locale: string,
    slug: string,
};

// Common page props shared by page components such as
// `account/pages/index` and `payments/pages/index`
export type PageProps = PageRoutesParams & {
    data: any,
};

type Props = {
    children: any,
};

const Page = ({ children }: Props) => (
    <>
        <A11yNav />
        <Header />
        {children}
        <Footer />
    </>
);

export default Page;
