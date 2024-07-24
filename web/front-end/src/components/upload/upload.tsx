import {
    FC, ReactNode, useEffect, useRef, useState
} from 'react';
import { addDocs, deleteDocs, FileState } from '@services/home';
import Button from '@components/button/button';
import { IconFont, Input, message } from 'sea-lion-ui';
import { useLocale } from '@hooks/useLocale';
import UploadItem, { UploadItemProps, UploadStatus } from '@components/upload-item';
import classNames from 'classnames';
import DeleteBtn from '@components/upload/delete-btn';
import styles from './upload.module.less';

export interface UploadProps {
    docs?: string[];
    afterUpload?: () => void;
    afterDelete?: () => void;
    filesState?: FileState[];
    children?: ReactNode;
}

interface FileItemProps {
    doc: string;
    color: string;
    state: string;
    checkedController: number;
    checkHandler?: (doc: string) => void;
}

const enum CheckedController {
    None = -1,
    Partial = 0,
    All = 1,
}

const acceptFileTypes = '.pdf,.txt,.md,.docx,.doc,.xlsx,.xls,.csv,.java,.cpp,.py,.js,.go,.html,.pptx';

const getBytesLength = (str) => {
    return new Blob([str]).size;
};

const FileItem: FC<FileItemProps> = (props) => {
    const {
        doc,
        color,
        state,
        checkedController,
        checkHandler
    } = props;

    const [checked, setChecked] = useState(false);

    const checkChange = (e) => {
        setChecked(e.target.checked);
        checkHandler(doc);
    };

    useEffect(() => {
        if (checkedController === CheckedController.None) {
            setChecked(false);
        }
        if (checkedController === CheckedController.All) {
            setChecked(true);
        }
    }, [checkedController]);

    return (
        <div className={styles.fileItem}>
            <input
                className={styles.checkbox}
                type="checkbox"
                checked={checked}
                onChange={checkChange}
            />
            <span
                style={{ color }}
                className={styles.fileState}
            >
                {state}
            </span>
            <span
                className={styles.fileName}
                title={doc}
            >
                {doc}
            </span>
        </div>
    );
};

const Upload: FC<UploadProps> = ({
    docs = [],
    afterUpload,
    afterDelete,
    filesState = [], children
}) => {
    const locales = useLocale('components');

    const fileInputRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [pendingFiles, setPendingFiles] = useState([]); // 待上传文件列表
    const [pendingStatus, setPendingStatus] = useState<UploadItemProps[]>([]); // 待上传文件列表
    const [filter, setFilter] = useState('');
    const [searchValue, setSearchValue] = useState('');

    const [checkedController, setCheckedController] = useState(CheckedController.Partial);
    const [checkedFiles, setCheckedFiles] = useState([]);

    const checkAll = (e) => {
        if (e.target.checked) {
            setCheckedController(CheckedController.All);
            setCheckedFiles(docs);
        } else {
            setCheckedController(CheckedController.None);
            setCheckedFiles([]);
        }
    };

    const checkItem = (doc) => {
        const _checkedFiles = [...checkedFiles];
        const index = _checkedFiles.indexOf(doc);
        if (index > -1) {
            _checkedFiles.splice(index, 1);
        } else {
            _checkedFiles.push(doc);
        }
        setCheckedFiles(_checkedFiles);
    };

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

    const deleteSelected = () => {
        if (checkedFiles.length === 0) {
            message.warning(locales.noSelected);
            return;
        }
        (async () => {
            const res: any = await deleteDocs(checkedFiles);
            if (res && res.docBase) {
                if (afterDelete) {
                    afterDelete();
                }
            }
        })();
    };

    useEffect(() => {
        if (checkedFiles.length === 0) {
            setCheckedController(CheckedController.None);
        } else if (checkedFiles.length === docs.length) {
            setCheckedController(CheckedController.All);
        } else {
            setCheckedController(CheckedController.Partial);
        }
    }, [checkedFiles]);

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
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <h4>{locales.uploadedFiles}</h4>
                {Array.isArray(docs) && docs.length > 0 && (
                    <div className={styles.checkboxWrapper}>
                        <input
                            type="checkbox"
                            className={classNames(styles.checkbox, {
                                [styles.mixedCheckbox]: checkedController === CheckedController.Partial
                            })}
                            checked={checkedController > CheckedController.None}
                            onChange={checkAll}
                        />
                        <span onClick={checkAll}>
                            {locales.selectAll}
                        </span>
                        <DeleteBtn onClick={deleteSelected} />
                    </div>
                )}
            </div>
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
                {/* 优先展示处理中文档 */}
                {docs
                    .filter((doc) => doc.includes(searchValue))
                    .filter((doc) => !filesState.find((file) => file.file === doc))
                    .map((doc) => {
                        return (
                            <FileItem
                                key={doc}
                                doc={doc}
                                color="#4e95e6"
                                state={locales.processing}
                                checkedController={checkedController}
                                checkHandler={checkItem}
                            />
                        );
                    })}
                {/* 按顺序显示已被处理的文档，有可能是失败状态 */}
                {filesState
                    .filter((file) => file.file.includes(searchValue))
                    .map((file) => (
                        <FileItem
                            key={file.file}
                            doc={file.file}
                            color={file.status ? undefined : 'red'}
                            state={file.desc || locales.uploadFailed}
                            checkedController={checkedController}
                            checkHandler={checkItem}
                        />
                    ))}
            </div>
        </>
    );
};

export default Upload;
