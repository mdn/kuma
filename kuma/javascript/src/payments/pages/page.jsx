// @flow
import * as React from 'react';
import A11yNav from '../../a11y/a11y-nav.jsx';
import Header from '../../header/header.jsx';
import Footer from '../../footer.jsx';

type Props = {
    children: any,
};

const Page = ({ children }: Props) => {
    return (
        <>
            <A11yNav />
            <Header />
            {children}
            <Footer />
        </>
    );
};

export default Page;
