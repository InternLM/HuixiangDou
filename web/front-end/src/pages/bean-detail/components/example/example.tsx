import {
    FC, ReactNode, useEffect, useState
} from 'react';
import {
    CountInput, IconFont, Input, Modal
} from 'sea-lion-ui';
import { useLocale } from '@hooks/useLocale';
import Button from '@components/button/button';
import { useParams } from 'react-router-dom';
import { getSampleInfo, updateSampleInfo } from '@services/home';
import styles from './example.module.less';

export interface ExampleProps {
    children?: ReactNode;
}

const Example: FC<ExampleProps> = () => {
    const beanId = decodeURI(useParams()?.beanName);
    const locales = useLocale('beanDetail');
    const [openModal, setOpenModal] = useState(false);
    const [negatives, setNegatives] = useState(['']);
    const [positives, setPositives] = useState(['']);
    const [inputValue, setInputValue] = useState('');

    useEffect(() => {
        if (openModal) {
            (async () => {
                const res = await getSampleInfo();
                if (res) {
                    setPositives(res.positives);
                    setNegatives(res.negatives);
                    setInputValue(res.negatives.join('\n'));
                }
            })();
        }
    }, [beanId, openModal]);

    const handleSave = async () => {
        const newNegatives = inputValue.split('\n');
        setNegatives(newNegatives);
        const res = await updateSampleInfo([''], newNegatives);
    };

    return (
        <div className={styles.example}>
            <Button onClick={() => setOpenModal(true)}>
                {locales.viewAndEdit}
                <IconFont icon="icon-FeedbackOutlined" />
            </Button>
            <Modal
                open={openModal}
                title="设置正反例"
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <div className={styles.editor}>
                    <CountInput
                        textarea
                        rows={12}
                        value={inputValue}
                        onChange={(e) => setInputValue(e)}
                    />
                </div>
                <Button onClick={handleSave}>保存</Button>
            </Modal>
        </div>
    );
};

export default Example;
