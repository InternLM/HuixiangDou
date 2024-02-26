import {
    FC, ReactNode, useRef, useState
} from 'react';
import { addDocs } from '@services/home';
import styles from './upload.module.less';

export interface UploadProps {
    files?: string[];
    children?: ReactNode;
}

const acceptFileTypes = '.jpg,.png,.jpeg,.bmp,.pdf,.txt,.md,.docx,.doc,.xlsx,.xls,.csv,.java,.cpp,.py,.js,.go';

const Upload: FC<UploadProps> = ({ files = [], children }) => {
    const fileInputRef = useRef(null);
    const [newFiles, setNewFiles] = useState([]);

    const handleClick = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const uploadFile = (e: any) => {
        const _newFiles = [...newFiles];
        for (let i = 0; i < e.target.files.length; i++) {
            const file = e.target.files[i];
            _newFiles.push(file.name);
            if (file.size > 1024 * 1024 * 100) {
                alert('文件大小不能超过100M');
                return;
            }
            addDocs(file)
                .catch(() => {
                    // remove the file from the list
                    setNewFiles(_newFiles.filter((f) => f !== file.name));
                });
        }
        setNewFiles(_newFiles);
    };

    return (
        <>
            <div className={styles.upload} onClick={handleClick}>
                <input
                    onChange={uploadFile}
                    ref={fileInputRef}
                    type="file"
                    accept={acceptFileTypes}
                    multiple
                    style={{ display: 'none' }}
                />
                {children}
            </div>
            <h4>新上传文档</h4>
            <div className={styles.fileList}>
                {newFiles.map((file) => (
                    <div key={file}>{file}</div>
                ))}
            </div>
            <h4>已上传文档</h4>
            <div className={styles.fileList}>
                {files.map((file) => (
                    <div key={file}>{file}</div>
                ))}
            </div>
        </>
    );
};

export default Upload;
