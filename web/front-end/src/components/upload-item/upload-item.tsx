import { FC } from 'react';
import { IconFont } from 'sea-lion-ui';
import { LoadingOutlined } from '@ant-design/icons';
import styles from './upload-item.module.less';

export const enum UploadStatus {
    init = 'init',
    done = 'done',
    uploading = 'uploading',
    error = 'error',
    removed = 'removed',
}

export interface UploadItemProps {
    uid: string;
    name: string;
    status: UploadStatus;
    progress: number;
}

const StatusColor = {
    init: 'lightgrey',
    done: 'green',
    uploading: 'blue',
    error: 'red',
    removed: 'darkgrey'
};

const StatusIcon = {
    init: 'icon-DocOutlined',
    done: 'icon-CheckCircleFilled',
    uploading: 'icon-HorizontalMoreOutlined',
    error: 'icon-CloseCircleFilled',
    removed: 'icon-DocOutlined'
};
const UploadItem: FC<UploadItemProps> = ({
    uid, name, status, progress
}) => {
    return (
        <div
            style={{
                border: `1px solid ${StatusColor[status]}`
            }}
            className={styles.uploadItem}
            key={uid}
        >
            <div className={styles.icon}>
                {status === UploadStatus.uploading ? <LoadingOutlined /> : (
                    <IconFont color={StatusColor[status]} icon={StatusIcon[status]} />
                )}
            </div>
            <div>
                <div className={styles.name}>{name}</div>
                <div className={styles.progress}>
                    <div
                        className={styles.bar}
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>
        </div>
    );
};

export default UploadItem;
