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
        const file = e.target.files[0];
        addDocs(file)
            .then((res) => {
                const docs = [...newFiles, res.docs];
                setNewFiles(docs);
            })
            .catch((err) => {
                console.log(err);
            });
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
            {newFiles.map((file) => (
                <div key={file}>{file}</div>
            ))}
            <h4>已上传文档</h4>
            {files.map((file) => (
                <div key={file}>{file}</div>
            ))}
        </>
    );
};

export default Upload;
