import { FC, ReactNode } from 'react';
import { notification } from '@components/notification/use-notification';
import EmojiWrapper from '@components/notification/emoji-wrapper';
import { useLocale } from '@hooks/useLocale';
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
    const locales = useLocale('components');

    return (
        <div className={styles.notification} id={notificationKey}>
            <div className={styles.title}>{title}</div>
            <div className={styles.content}>{content}</div>
            <div className={styles.footer}>
                <div
                    className={styles.cancel}
                    onClick={() => notification.unmountNotification(notificationKey)}
                >
                    {locales.hide4ever}
                </div>
                <EmojiWrapper>
                    <div
                        className={styles.confirm}
                        onClick={() => {
                            window.open('https://github.com/InternLM/HuixiangDou/');
                        }}
                    >
                        {locales.goStar}
                    </div>
                </EmojiWrapper>
            </div>
        </div>
    );
};

export default Notification;
