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
    const [loading, setLoading] = useState(false);

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
        setLoading(true);
        const newNegatives = negatives.split('\n');
        const newPositives = positives.split('\n');
        updateSampleInfo(newPositives, newNegatives).finally(() => {
            setLoading(false);
        });
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
                                    placeholder={`正例是真实场景中，来自提问者的、须答复的问题，每句话一行，例如：
你好，我是实习生，请问单位有宿舍么？
你们的产品和友商对比有啥优势啊？`}
                                    onChange={(e) => setPositives(e)}
                                />
                            </div>
                            <Button onClick={handleSave}>{loading ? 'Saving...' : '保存'}</Button>
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
                                    placeholder={`反例是真实场景中的闲聊，不应该答复。
每句一行，例如：
今天中午吃日料么？
快看天上有颗流星，快跑`}
                                    onChange={(e) => setNegatives(e)}
                                />
                            </div>
                            <Button onClick={handleSave}>{loading ? 'Saving...' : '保存'}</Button>
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
