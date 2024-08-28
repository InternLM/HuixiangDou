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
                    label: locales.setPositive,
                    children: (
                        <>
                            <div className={styles.editor}>
                                <CountInput
                                    textarea
                                    rows={12}
                                    value={positives}
                                    placeholder={locales.positiveDesc}
                                    onChange={(e) => setPositives(e)}
                                />
                            </div>
                            <Button onClick={handleSave}>
                                {
                                    loading ? locales.saving : locales.save
                                }
                            </Button>
                        </>
                    ),
                },
                {
                    key: 'negatives',
                    label: locales.setNegative,
                    children: (
                        <>
                            <div className={styles.editor}>
                                <CountInput
                                    textarea
                                    rows={12}
                                    value={negatives}
                                    placeholder={locales.negativeDesc}
                                    onChange={(e) => setNegatives(e)}
                                />
                            </div>
                            <Button onClick={handleSave}>
                                {
                                    loading ? locales.saving : locales.save
                                }
                            </Button>
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
                title={locales.addExamples}
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <Tabs items={items} />
            </Modal>
        </div>
    );
};

export default Example;
