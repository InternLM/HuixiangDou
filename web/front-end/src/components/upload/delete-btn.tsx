import { IconFont, Modal } from 'sea-lion-ui';
import { useLocale } from '@hooks/useLocale';
import { useState } from 'react';
import styles from './upload.module.less';

const DeleteBtn = ({ onClick }) => {
    const locales = useLocale('components');

    const [openModal, setOpenModal] = useState(false);

    const handleClick = () => {
        setOpenModal(true);
    };

    const confirm = () => {
        setOpenModal(false);
        onClick();
    };

    const cancel = () => {
        setOpenModal(false);
    };

    return (
        <>
            <div className={styles.delete} onClick={handleClick}>
                <IconFont icon="icon-shanchu" />
                {locales.deleteSelected}
            </div>
            <Modal
                closeable={false}
                open={openModal}
                title={locales.deleteConfirm}
                footer={(<div />)}
                icon={<IconFont icon="icon-AttentionOutlined" style={{ color: 'red', fontSize: 20 }} />}
                onClose={() => setOpenModal(false)}
            >
                <div>{locales.deleteDesc}</div>
                <div className={styles.modalFooter}>
                    <div onClick={confirm} className={styles.confirm}>{locales.confirm}</div>
                    <div onClick={cancel} className={styles.cancel}>{locales.cancel}</div>
                </div>
            </Modal>
        </>

    );
};

export default DeleteBtn;
