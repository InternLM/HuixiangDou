import Header from '@components/header/header';
import BodyLayout from '@layouts/header-container-layout/body-layout';
import styles from './header-container-layout.module.less';

const HeaderContainerLayout = () => {
    return (
        <div className={styles.wrapper}>
            <Header />
            <BodyLayout />
        </div>
    );
};

export default HeaderContainerLayout;
