import { Outlet } from 'react-router-dom';
import Header from '@components/header/header';
import useNotification from '@components/notification/use-notification';
import styles from './header-container-layout.module.less';

const HeaderContainerLayout = () => {
    useNotification();

    return (
        <div className={styles.wrapper}>
            <Header />
            <div className={styles.body}>
                <Outlet />
            </div>
        </div>
    );
};

export default HeaderContainerLayout;
