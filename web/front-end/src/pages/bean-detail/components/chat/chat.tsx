import {
    FC, ReactNode, useEffect, useRef, useState
} from 'react';
import Button from '@components/button/button';
import { online, onlineResponse } from '@services/home';
import styles from './chat.module.less';

export interface ChatProps {
    children?: ReactNode;
}

export interface Message {
    'sender': number,
    'content': string,
    'code': number,
    'state': string,
    'references': string[]
}

const Chat: FC<ChatProps> = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [queryId, setQueryId] = useState(''); // 查询回复id

    const editorRef = useRef<HTMLDivElement>(null);

    const handleSendMessage = async () => {
        // read all images as file from the editor
        const images = [''];

        const currPrompt = editorRef.current.innerText;
        const history = messages.map((item) => {
            return {
                content: item.content,
                sender: item.sender,
            };
        });
        editorRef.current.innerHTML = '';
        const res = await online({
            content: currPrompt,
            history,
            images,
        });
        if (res) {
            setQueryId(res.queryId);
        }
    };

    useEffect(() => {
        let id;
        if (queryId) {
            // polling for response
            id = setInterval(async () => {
                const res = await onlineResponse(queryId);
                if (res) {
                    // 如果回复成功且有回复内容；或者回复失败，停止轮询
                    if ((res.code === 0 && res.text) || res.code > 0) {
                        clearInterval(id);
                    }
                }
            }, 2000);
        }
        return () => {
            clearInterval(id);
        };
    }, [queryId]);

    return (
        <div className={styles.chat}>
            <div className={styles.messageList}>
                {messages.map((message, index) => (
                    <div className={styles.message} key={message.key}>
                        {message.sender === 0 ? '用户' : '机器人'}
                        {message.content}
                    </div>
                ))}
            </div>
            <div className={styles.inputWrapper}>
                <div className={styles.editorWrapper}>
                    <div
                        contentEditable
                        spellCheck
                        ref={editorRef}
                        id="prompt-textarea"
                        className={styles.promptEditor}
                        data-text="placeholder"
                    />
                </div>
                <Button
                    disabled={queryId}
                    onClick={handleSendMessage}
                >
                    发送
                </Button>
            </div>
        </div>
    );
};

export default Chat;
