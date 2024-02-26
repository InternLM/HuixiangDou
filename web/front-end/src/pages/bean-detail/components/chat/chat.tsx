import { FC, ReactNode, useState } from 'react';
import Button from '@components/button/button';
import { Input } from 'sea-lion-ui';
import styles from './chat.module.less';

export interface ChatProps {
    children?: ReactNode;
}

const Chat: FC<ChatProps> = () => {
    const [messages, setMessages] = useState([]);
    return (
        <div className={styles.chat}>
            <div className={styles.messageList}>
                {messages.map((message, index) => (
                    <div className={styles.message} key={message.key}>{message}</div>
                ))}
            </div>
            <div className={styles.inputWrapper}>
                <Input />
                <Button>发送</Button>
            </div>
        </div>
    );
};

export default Chat;
