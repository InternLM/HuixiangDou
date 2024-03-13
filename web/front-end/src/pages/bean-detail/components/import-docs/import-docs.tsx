import {
    FC, ReactNode, useState
} from 'react';
import { IconFont, Modal } from 'sea-lion-ui';
import Button from '@components/button/button';
import { useLocale } from '@hooks/useLocale';
import Upload from '@components/upload';
import { FileState } from '@services/home';
import styles from './import-docs.module.less';

export interface ImportDocsProps {
    filesState: FileState[];
    refresh: () => void;
    docs?: string[];
    children?: ReactNode;
}

const ImportDocs: FC<ImportDocsProps> = ({ refresh, docs, filesState }) => {
    const locales = useLocale('beanDetail');
    const [openModal, setOpenModal] = useState(false);

    const afterUpload = () => {
        refresh();
    };
    return (
        <div className={styles.importDocs}>
            <Button onClick={() => setOpenModal(true)}>
                {locales.docs}
                <IconFont icon="icon-DocOutlined" />
            </Button>
            <Modal
                maskClosable={false}
                open={openModal}
                title={locales.addDocs}
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <Upload docs={docs} filesState={filesState} afterUpload={afterUpload}>
                    <IconFont icon="icon-PlusOutlined" />
                    <div>{locales.upload}</div>
                    <div>{locales.supportFiles}</div>
                </Upload>
            </Modal>
        </div>
    );
};

export default ImportDocs;
