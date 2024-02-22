import {
    FC, ReactNode, useEffect, useState
} from 'react';
import { IconFont, Modal } from 'sea-lion-ui';
import { useLocale } from '@hooks/useLocale';
import Button from '@components/button/button';
import { useParams } from 'react-router-dom';
import { getSampleInfo } from '@services/home';
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

    useEffect(() => {
        (async () => {
            const res = await getSampleInfo();
            if (res) {
                setPositives(res.positives);
                setNegatives(res.negatives);
            }
        })();
    }, [beanId]);

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
                <div>
                    {positives.map((item) => (
                        <div>{item || 'xxx'}</div>
                    ))}
                </div>
            </Modal>
        </div>
    );
};

export default Example;
