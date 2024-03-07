import Notification, { NotificationProps } from '@components/notification/notification';
import { useLocale } from '@hooks/useLocale';
import ComponentPortal from '@components/components-portal/components-portal';

const notificationWrapper = 'global-notification';

export const notification = {
    notificationContainer: null,

    showNotification(params: NotificationProps) {
        if (document.getElementById(notificationWrapper)) {
            document.body.removeChild(document.getElementById(notificationWrapper));
            this.notificationContainer = null;
        }
        if (localStorage.getItem(params.notificationKey)) {
            return null;
        }
        this.notificationContainer = document.createElement('div');
        this.notificationContainer.id = notificationWrapper;
        document.body.appendChild(this.notificationContainer);
        return (
            <ComponentPortal wrapperId={notificationWrapper}>
                <Notification {...params} />
            </ComponentPortal>
        );
    },
    unmountNotification(key) {
        if (this.notificationContainer) {
            localStorage.setItem(key, 'true');
            document.body.removeChild(this.notificationContainer);
            this.notificationContainer = null;
        }
    },
};
const useNotification = () => {
    const locales = useLocale('components');

    return notification.showNotification({
        title: '',
        content: locales.notificationContent,
        notificationKey: '__HuiXiangDou__',
    });
};

export default useNotification;
