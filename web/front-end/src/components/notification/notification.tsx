import { FC, ReactNode } from 'react';
import { notification } from '@components/notification/use-notification';
import EmojiWrapper from '@components/notification/emoji-wrapper';
import styles from './notification.module.less';

export interface NotificationProps {
    title: string;
    content: string;
    notificationKey: string;
    children?: ReactNode;
}

const Notification: FC<NotificationProps> = ({
    title,
    content,
    notificationKey,
}) => {
    return (
        <div className={styles.notification} id={notificationKey}>
            <div className={styles.title}>{title}</div>
            <div className={styles.content}>{content}</div>
            <div className={styles.footer}>
                <div
                    className={styles.cancel}
                    onClick={() => notification.unmountNotification(notificationKey)}
                >
                    不再显示
                </div>
                <EmojiWrapper>
                    <div
                        className={styles.confirm}
                        onClick={() => {
                            window.open('https://github.com/InternLM/HuixiangDou/');
                        }}
                    >
                        前往鼓励
                    </div>
                </EmojiWrapper>
            </div>
        </div>
    );
};

export default Notification;
