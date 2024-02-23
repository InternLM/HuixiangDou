import {
    FC, ReactNode, useEffect, useState
} from 'react';
import { IconFont, Modal } from 'sea-lion-ui';
import Button from '@components/button/button';
import { useLocale } from '@hooks/useLocale';
import Upload from '@components/upload';
import { getInfo } from '@services/home';
import styles from './import-docs.module.less';

export interface ImportDocsProps {
    children?: ReactNode;
}

const ImportDocs: FC<ImportDocsProps> = () => {
    const locales = useLocale('beanDetail');
    const [openModal, setOpenModal] = useState(false);
    const [files, setFiles] = useState(['']);

    useEffect(() => {
        if (openModal) {
            (async () => {
                const res = await getInfo();
                if (res) {
                    setFiles(res.docs);
                }
            })();
        }
    }, [openModal]);

    return (
        <div className={styles.importDocs}>
            <Button onClick={() => setOpenModal(true)}>
                {locales.docs}
                <IconFont icon="icon-DocOutlined" />
            </Button>
            <Modal
                open={openModal}
                title={locales.addDocs}
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <Upload files={files}>
                    <IconFont icon="icon-PlusOutlined" />
                    <div>{locales.upload}</div>
                </Upload>
            </Modal>
        </div>
    );
};

export default ImportDocs;
