import { Outlet } from 'react-router-dom';
import useNotification from '@components/notification/use-notification';
import { useLocale } from '@hooks/useLocale';
import styles from './header-container-layout.module.less';

const BodyLayout = () => {
    const locales = useLocale('components');
    useNotification();

    return (
        <div className={styles.body} id="root-body">
            <Outlet />
        </div>
    );
};

export default BodyLayout;
