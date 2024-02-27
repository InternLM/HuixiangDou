import {
    FC, ReactNode, useEffect, useRef, useState
} from 'react';
import { addDocs } from '@services/home';
import Button from '@components/button/button';
import styles from './upload.module.less';

export interface UploadProps {
    files?: string[];
    children?: ReactNode;
}

const acceptFileTypes = '.jpg,.png,.jpeg,.bmp,.pdf,.txt,.md,.docx,.doc,.xlsx,.xls,.csv,.java,.cpp,.py,.js,.go';

const Upload: FC<UploadProps> = ({ files = [], children }) => {
    const fileInputRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [newFiles, setNewFiles] = useState(files); // 已上传文件列表
    const [pendingFiles, setPendingFiles] = useState([]); // 待上传文件列表

    const handleClick = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const onFileChange = (e) => {
        setPendingFiles([...pendingFiles, ...e.target.files]);
    };

    const uploadFile = () => {
        setLoading(true);
        addDocs(pendingFiles)
            .then((res) => {
                setPendingFiles([]);
                setNewFiles([...newFiles, ...res.docs]);
            })
            .finally(() => {
                setLoading(false);
            });
    };

    useEffect(() => {
        setNewFiles(files);
    }, [files]);

    return (
        <>
            <div className={styles.upload} onClick={handleClick}>
                <input
                    onChange={onFileChange}
                    ref={fileInputRef}
                    type="file"
                    accept={acceptFileTypes}
                    multiple
                    max={10}
                    style={{ display: 'none' }}
                />
                {children}
            </div>
            <div className={styles.desc}>上传时可以框选多个文件</div>
            <h4>待上传文档</h4>
            <div className={styles.fileList}>
                {pendingFiles.map((file) => (
                    <div key={file}>{file.name}</div>
                ))}
            </div>
            {pendingFiles.length > 0 && (
                <Button onClick={uploadFile}>{loading ? 'Uploading...' : '确认上传'}</Button>
            )}
            <h4>已上传文档</h4>
            <div className={styles.fileList}>
                {newFiles.map((file) => (
                    <div key={file}>{file}</div>
                ))}
            </div>
        </>
    );
};

export default Upload;
