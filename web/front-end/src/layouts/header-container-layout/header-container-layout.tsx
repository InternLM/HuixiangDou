import Header from '@components/header/header';
import { Outlet } from 'react-router-dom';
import useNotification from '@components/notification/use-notification';
import styles from './header-container-layout.module.less';

const HeaderContainerLayout = () => {
    return (
        <div className={styles.wrapper}>
            <Header />
            <div className={styles.body} id="root-body">
                <Outlet />
            </div>
            {useNotification()}
        </div>
    );
};

export default HeaderContainerLayout;
