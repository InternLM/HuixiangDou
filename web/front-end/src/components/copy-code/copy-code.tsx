import { IconFont, message } from 'sea-lion-ui';
import styles from './copy-code.module.less';

export interface CopyCodeProps {
    code: string;
}

const CopyCode = (props: CopyCodeProps) => {
    const { code } = props;
    const copy = () => {
        const input = document.createElement('input');
        input.value = code;
        document.body.appendChild(input);
        input.select();
        document.execCommand('copy');
        message.success('复制成功');
        document.body.removeChild(input);
    };
    return (
        <div className={styles.copyCode}>
            <div className={styles.code}>{code}</div>
            <div className={styles.copy} onClick={copy}>
                <IconFont icon="icon-CopyOutlined" />
            </div>
        </div>
    );
};

export default CopyCode;
