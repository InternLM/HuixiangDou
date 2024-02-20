import { Outlet } from 'react-router-dom';
import Header from '@components/header/header';
import styles from './header-container-layout.module.less';

const HeaderContainerLayout = () => {
    return (
        <div className={styles.wrapper}>
            <div className={styles.header}>
                <Header />
            </div>
            <div className={styles.body}>
                <Outlet />
            </div>
        </div>
    );
};

export default HeaderContainerLayout;
