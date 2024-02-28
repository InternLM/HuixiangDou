import { FC, ReactNode } from 'react';
import styles from './notification.module.less';

interface EmojiWrapperProps {
    emoji?: string;
    children?: ReactNode;
}

const heart = 'https://oss.openmmlab.com/www/home/heart_3d.png';
const EmojiWrapper: FC<EmojiWrapperProps> = ({ emoji = heart, children }) => {
    return (
        <div className={styles.emojiWrapper}>
            {children}
            <img src={emoji} className={styles.emoji1} />
            <img src={emoji} className={styles.emoji2} />
            <img src={emoji} className={styles.emoji3} />
        </div>
    );
};

export default EmojiWrapper;
