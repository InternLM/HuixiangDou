import {
    FC, ReactNode, useRef, useState
} from 'react';
import { addDocs, FileState } from '@services/home';
import Button from '@components/button/button';
import { message } from 'sea-lion-ui';
import { useLocale } from '@hooks/useLocale';
import UploadItem, { UploadItemProps, UploadStatus } from '@components/upload-item';
import styles from './upload.module.less';

export interface UploadProps {
    docs?: string[];
    afterUpload?: () => void;
    filesState?: FileState[];
    children?: ReactNode;
}

const acceptFileTypes = '.pdf,.txt,.md,.docx,.doc,.xlsx,.xls,.csv,.java,.cpp,.py,.js,.go';

const Upload: FC<UploadProps> = ({
    docs = [],
    afterUpload,
    filesState = [], children
}) => {
    const locales = useLocale('components');

    const fileInputRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [pendingFiles, setPendingFiles] = useState([]); // 待上传文件列表
    const [pendingStatus, setPendingStatus] = useState<UploadItemProps[]>([]); // 待上传文件列表

    const handleClick = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const onFileChange = (e) => {
        const _files = e.target.files;
        const _pendingStatus = [...pendingStatus];
        const _pendingFiles = [...pendingFiles];
        for (let i = 0; i < _files.length; i++) {
            if (_files[i].size > 1024 * 1024 * 1000) {
                message.warning(locales.fileSize);
                setLoading(false);
                return;
            }
            _pendingFiles.push(_files[i]);
            _pendingStatus.push({
                uid: `${new Date().getTime()}_${_files[i].name}`,
                name: _files[i].name,
                status: UploadStatus.init,
                progress: 0,
            });
        }
        setPendingFiles([..._pendingFiles]);
        setPendingStatus([..._pendingStatus]);
    };

    const uploadFile = () => {
        setLoading(true);
        const _pendingStatus = [...pendingStatus];

        _pendingStatus.forEach((item) => {
            if (item.status !== UploadStatus.done) {
                item.status = UploadStatus.uploading;
            }
        });
        setPendingStatus(_pendingStatus);

        addDocs(pendingFiles)
            .then((res) => {
                if (res && Array.isArray(res.docs)) {
                    _pendingStatus.forEach((item) => {
                        if (item.status === UploadStatus.uploading && res.docs.includes(item.name)) {
                            item.status = UploadStatus.done;
                            item.progress = 100;
                        } else {
                            item.status = UploadStatus.error;
                            item.progress = 0;
                        }
                    });
                    setTimeout(() => {
                        setPendingStatus([]);
                    }, 2000);
                } else {
                    _pendingStatus.forEach((item) => {
                        if (item.status === UploadStatus.uploading) {
                            item.status = UploadStatus.error;
                            item.progress = 0;
                        }
                    });
                }
                setPendingStatus(_pendingStatus);
                setPendingFiles([]);
                if (afterUpload) {
                    afterUpload();
                }
            })
            .catch(() => {
                _pendingStatus.forEach((item) => {
                    if (item.status === UploadStatus.uploading) {
                        item.status = UploadStatus.error;
                        item.progress = 0;
                    }
                });
                setPendingStatus(_pendingStatus);
            })
            .finally(() => {
                setLoading(false);
            });
    };

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
            <h4>{locales.pendingFiles}</h4>
            <div className={styles.fileList}>
                {pendingStatus.map((file) => (
                    <UploadItem {...file} />
                ))}
            </div>
            {pendingFiles.length > 0 && (
                <Button onClick={uploadFile}>{loading ? locales.uploading : locales.confirmUpload}</Button>
            )}
            <h4>{locales.uploadedFiles}</h4>
            <div className={styles.fileList}>
                <div>
                    {`${locales.total}: ${filesState.length},    `}
                    {`${locales.failed}: ${filesState.filter((file) => !file.status).length}`}
                </div>
                {docs
                    .filter((doc) => !filesState.find((file) => file.file === doc))
                    .map((doc) => {
                        return (
                            <div
                                key={doc}
                                className={styles.fileItem}
                            >
                                <span
                                    style={{ color: '#4e95e6' }}
                                    className={styles.fileState}
                                    title={doc}
                                >
                                    {locales.processing}
                                </span>
                                <span className={styles.fileName}>{doc}</span>
                            </div>
                        );
                    })}
                {filesState.map((file) => (
                    <div
                        key={file.file}
                        className={styles.fileItem}
                    >
                        <span
                            style={{ color: file.status ? undefined : 'red' }}
                            className={styles.fileState}
                            title={file.desc}
                        >
                            {file.desc || locales.uploadFailed}
                        </span>
                        <span className={styles.fileName}>{file.file}</span>
                    </div>
                ))}
            </div>
        </>
    );
};

export default Upload;
