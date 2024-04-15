import {
    FC, ReactNode, useRef, useState
} from 'react';
import { addDocs, FileState } from '@services/home';
import Button from '@components/button/button';
import { Input, message } from 'sea-lion-ui';
import { useLocale } from '@hooks/useLocale';
import UploadItem, { UploadItemProps, UploadStatus } from '@components/upload-item';
import styles from './upload.module.less';

export interface UploadProps {
    docs?: string[];
    afterUpload?: () => void;
    filesState?: FileState[];
    children?: ReactNode;
}

const acceptFileTypes = '.pdf,.txt,.md,.docx,.doc,.xlsx,.xls,.csv,.java,.cpp,.py,.js,.go,.html,.pptx';

const getBytesLength = (str) => {
    return new Blob([str]).size;
};

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
    const [filter, setFilter] = useState('');
    const [searchValue, setSearchValue] = useState('');

    const handleSearch = () => {
        setSearchValue(filter);
    };

    const handleClick = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    const onFileChange = (e) => {
        const _files = e.target.files;
        const _pendingStatus = [...pendingStatus];
        const _pendingFiles = [...pendingFiles];
        if (_files.length > 200) {
            message.warning(locales.fileCount);
            setLoading(false);
            return;
        }
        for (let i = 0; i < _files.length; i++) {
            // Validate file name's byte length
            if (getBytesLength(_files[i].name) > 255) {
                message.warning(locales.nameSize);
                setLoading(false);
                return;
            }
            // Validate file size
            if (_files[i].size > 1024 * 1024 * 35) {
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
                        } else if (item.status === UploadStatus.uploading) {
                            item.status = UploadStatus.error;
                            item.progress = 0;
                        }
                    });
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
                <div className={styles.fileSearch}>
                    <Input
                        placeholder={locales.searchDesc}
                        value={filter}
                        onChange={(e) => setFilter(e.target.value)}
                        onPressEnter={handleSearch}
                    />
                    <Button onClick={handleSearch}>
                        {locales.search}
                    </Button>
                </div>
                {docs
                    .filter((doc) => doc.includes(searchValue))
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
                                >
                                    {locales.processing}
                                </span>
                                <span
                                    className={styles.fileName}
                                    title={doc}
                                >
                                    {doc}
                                </span>
                            </div>
                        );
                    })}
                {filesState
                    .filter((file) => file.file.includes(searchValue))
                    .map((file) => (
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
                            <span
                                className={styles.fileName}
                                title={file.file}
                            >
                                {file.file}
                            </span>
                        </div>
                    ))}
            </div>
        </>
    );
};

export default Upload;
