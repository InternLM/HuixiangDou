import { useEffect } from 'react';
import ReactDOM from 'react-dom/client';
import Notification, { NotificationProps } from '@components/notification/notification';

let notificationContainer = null;

export const notification = {
    showNotification(params: Omit<NotificationProps, 'children'>) {
        if (localStorage.getItem(params.notificationKey)) {
            return;
        }
        if (!document.getElementById('global-notification')) {
            notificationContainer = document.createElement('div');
            notificationContainer.id = 'global-notification';
            document.body.appendChild(notificationContainer);
            ReactDOM.createRoot(notificationContainer).render(<Notification {...params} />);
        }
    },

    unmountNotification(key) {
        if (notificationContainer) {
            localStorage.setItem(key, 'true');
            ReactDOM.hydrateRoot(notificationContainer, null);
            document.body.removeChild(notificationContainer);
        }
    },
};
const useNotification = () => {
    useEffect(() => {
        notification.showNotification({
            title: '',
            content: `🎉HuixiangDou开源啦，快来给我们 star 吧!
小时候，我想当开源人，朋友给我鼓励和我最爱的小星星🌟 🥺`,
            notificationKey: '__HuiXiangDou__',
        });
    }, []);
};

export default useNotification;
