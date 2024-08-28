import {
    FC, ReactNode, useEffect, useRef, useState
} from 'react';
import Button from '@components/button/button';
import { caseFeedback, online, onlineResponse } from '@services/home';
import bean from '@assets/imgs/bean1.png';
import { useLocale } from '@hooks/useLocale';
import styles from './chat.module.less';

export interface ChatProps {
    children?: ReactNode;
}

export interface Message {
    queryId?: string,
    sender: number,
    content: string,
    code: number,
    state: string,
    images: string[],
    references: string[]
}

export const enum Feedback {
    good = 1,
    bad = 0
}

function MessageItem(props: { message: Message }) {
    const locales = useLocale('beanDetail');

    const [feedback, setFeedback] = useState('');
    const [maxWidth, setMaxWidth] = useState(24);
    if (!props.message) {
        return null;
    }
    const {
        state,
        sender,
        content,
        images,
        references,
        queryId
    } = props.message;

    const sendFeedback = async (type: string) => {
        const res = await caseFeedback(queryId, type);
    };

    return (
        <div className={styles.messageWrapper}>
            <div className={styles.avatar}>
                {sender === 0 ? '🤓' : (
                    <img src={bean} alt="bean" />
                )}
            </div>
            <div className={styles.message} style={{ background: sender === 1 ? '#EDFFEA' : '#f0f0f0' }}>
                <div className={styles.imgWrapper}>
                    {Array.isArray(images)
                        && images.length > 0
                        && images.map((img) => (
                            <img src={img} style={{ height: 24 }} alt="img" />
                        ))}
                </div>
                <div>{content}</div>
                {Array.isArray(references) && references.length > 0 && (
                    <div className={styles.referenceWrapper}>
                        {locales.references}
                        <div className={styles.reference}>
                            {references.join('\n')}
                        </div>
                    </div>
                )}
                {state && state.toLowerCase() !== 'success' && (
                    <div className={styles.reference}>
                        [Empty]:
                        {' '}
                        {state}
                    </div>
                )}
                {queryId && sender === 1 && (
                    <div
                        style={{ maxWidth }}
                        className={styles.footer}
                        onMouseEnter={() => {
                            setMaxWidth(200);
                        }}
                        onMouseLeave={() => {
                            setMaxWidth(24);
                        }}
                    >
                        <div
                            className={styles.feedback}
                            style={{ background: '#e3e3e3' }}
                        >
                            {feedback || '💬'}
                        </div>
                        {feedback !== '👍' && (
                            <div
                                className={styles.feedback}
                                style={{ background: feedback === '👍' ? '#e3e3e3' : undefined }}
                                onClick={() => {
                                    if (!feedback) {
                                        setFeedback('👍');
                                        sendFeedback('good');
                                    }
                                }}
                            >
                                👍
                            </div>
                        )}
                        {feedback !== '👎' && (
                            <div
                                className={styles.feedback}
                                style={{ background: feedback === '👎' ? '#e3e3e3' : undefined }}
                                onClick={() => {
                                    if (!feedback) {
                                        setFeedback('👎');
                                        sendFeedback('bad');
                                    }
                                }}
                            >
                                👎
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

const Chat: FC<ChatProps> = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [queryId, setQueryId] = useState(''); // 查询回复id
    const [isComposing, setIsComposing] = useState(false);
    const messageListRef = useRef(null);

    const locales = useLocale('beanDetail');

    const editorRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        if (messageListRef.current) {
            messageListRef.current.scrollTo({ top: 999999, behavior: 'smooth' });
        }
    };

    const handleSendMessage = async () => {
        if (queryId) {
            return;
        }

        // read all images' base64 code from the editor
        const imgNodes = editorRef.current.querySelectorAll('img');
        const images = Array.from(imgNodes).map((node) => {
            return node.src;
        });
        const currPrompt = editorRef.current.innerText.trim();
        // if no prompt and no images, return
        if (!currPrompt && images.length === 0) {
            return;
        }
        const history = messages.map((item) => {
            return {
                content: item.content,
                sender: item.sender,
            };
        });
        const newMessage = {
            sender: 0,
            content: currPrompt,
            code: undefined,
            state: '',
            images,
            references: [],
        };
        setMessages([...messages, newMessage]);
        scrollToBottom();
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

    const handleKeyDown = (e) => {
        const key = e.code;
        if (!isComposing && key === 'Enter' && !e.shiftKey) {
            handleSendMessage();
            e.preventDefault();
        }
    };

    useEffect(() => {
        let b;
        if (queryId) {
            // polling for response
            let pollingTimes = 0;
            const pendingMessage = {
                sender: 1,
                content: '...',
                code: undefined,
                state: '',
                images: [],
                references: [],
            };
            setMessages([...messages, pendingMessage]);
            scrollToBottom();
            b = setInterval(() => {
                pollingTimes += 1;
                onlineResponse(queryId)
                    .then((res) => {
                        if (res) {
                            // 如果回复成功且有回复内容；或者回复失败，停止轮询
                            if ((res.code === 0 && res.text) || res.code > 0) {
                                clearInterval(b);
                                setQueryId('');
                                const newMessage = {
                                    queryId,
                                    sender: 1,
                                    content: res.text,
                                    code: res.code,
                                    state: res.state,
                                    images: [],
                                    references: res.references,
                                };
                                setMessages([...messages, newMessage]);
                                scrollToBottom();
                            }
                        }
                    })
                    .catch((err) => {
                        console.error(err);
                        clearInterval(b);
                        setQueryId('');
                    });
                if (pollingTimes === 60) {
                    const newMessage = {
                        queryId,
                        sender: 1,
                        content: locales.timeout,
                        code: 0,
                        state: '',
                        images: [],
                        references: [],
                    };
                    clearInterval(b);
                    setQueryId('');
                    setMessages([...messages, newMessage]);
                    scrollToBottom();
                }
            }, 3000);
        }
        return () => {
            clearInterval(b);
        };
    }, [queryId]);

    return (
        <div className={styles.chat}>
            <div className={styles.messageList} ref={messageListRef}>
                {messages.map((message, index) => (
                    <MessageItem
                        key={message.content + index}
                        message={message}
                    />
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
                        onKeyDown={handleKeyDown}
                        onCompositionStart={() => setIsComposing(true)}
                        onCompositionEnd={() => setIsComposing(false)}
                        aria-placeholder={locales.inputPlaceholder}
                    />
                </div>
                <Button
                    disabled={!!queryId}
                    onClick={handleSendMessage}
                >
                    {locales.send}
                </Button>
            </div>
        </div>
    );
};

export default Chat;
