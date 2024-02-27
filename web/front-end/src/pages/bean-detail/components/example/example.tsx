import {
    FC, ReactNode, useEffect, useMemo, useState
} from 'react';
import {
    CountInput, IconFont, Modal
} from 'sea-lion-ui';
import { Tabs } from 'antd';
import type { TabsProps } from 'antd';
import { useLocale } from '@hooks/useLocale';
import Button from '@components/button/button';
import { getSampleInfo, updateSampleInfo } from '@services/home';
import styles from './example.module.less';

export interface ExampleProps {
    children?: ReactNode;
}

const Example: FC<ExampleProps> = () => {
    const locales = useLocale('beanDetail');
    const [openModal, setOpenModal] = useState(false);
    const [negatives, setNegatives] = useState('');
    const [positives, setPositives] = useState('');

    useEffect(() => {
        if (openModal) {
            (async () => {
                const res = await getSampleInfo();
                if (res) {
                    setPositives(res.positives.join('\n'));
                    setNegatives(res.negatives.join('\n'));
                }
            })();
        }
    }, [openModal]);

    const handleSave = async () => {
        const newNegatives = negatives.split('\n');
        const newPositives = positives.split('\n');
        setNegatives(newNegatives);
        const res = await updateSampleInfo(newPositives, newNegatives);
    };

    const items: TabsProps['items'] = useMemo(() => {
        return (
            [
                {
                    key: 'positives',
                    label: '设置正例',
                    children: (
                        <>
                            <div className={styles.editor}>
                                <CountInput
                                    textarea
                                    rows={12}
                                    value={positives}
                                    onChange={(e) => setPositives(e)}
                                />
                            </div>
                            <Button onClick={handleSave}>保存</Button>
                        </>
                    ),
                },
                {
                    key: 'negatives',
                    label: '设置反例',
                    children: (
                        <>
                            <div className={styles.editor}>
                                <CountInput
                                    textarea
                                    rows={12}
                                    value={negatives}
                                    onChange={(e) => setNegatives(e)}
                                />
                            </div>
                            <Button onClick={handleSave}>保存</Button>
                        </>
                    ),
                },
            ]
        );
    }, [negatives, positives, handleSave]);

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
                <Tabs items={items} />
            </Modal>
        </div>
    );
};

export default Example;
