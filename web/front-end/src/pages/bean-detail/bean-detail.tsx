import {
    FC, ReactNode, useEffect, useMemo, useState
} from 'react';
import { useLocale } from '@hooks/useLocale';
import { useParams } from 'react-router-dom';
import { IconFont } from 'sea-lion-ui';
import logo from '@assets/imgs/logo.png';
import bean from '@assets/imgs/bean.png';
import Chat from '@pages/bean-detail/components/chat';
import { Feishu, getInfo } from '@services/home';
import ToggleSearch from '@pages/bean-detail/components/toggle-search';
import Example from '@pages/bean-detail/components/example';
import ImportDocs from '@pages/bean-detail/components/import-docs';
import IntegrateFeishu from '@pages/bean-detail/components/integrate-feishu';
import styles from './bean-detail.module.less';

export interface BeanDetailProps {
    children?: ReactNode;
}

export enum BeanState {
    'failed' = -1,
    'created' = 0,
    'finished' = 2,
}

const BeanDetail: FC<BeanDetailProps> = () => {
    const locales = useLocale('beanDetail');
    const [name, setName] = useState('');
    const [weChatInfo, setWeChatInfo] = useState(null);
    const [searchToken, setSearchToken] = useState('');
    const [beanState, setBeanState] = useState(null);

    const state = {
        [BeanState.failed]: locales.createFailed,
        [BeanState.created]: locales.created,
        [BeanState.finished]: locales.createSuccess,
    };
    const color = {
        [BeanState.failed]: '#f1bcbc',
        [BeanState.created]: '#ffe2bf',
        [BeanState.finished]: '#e3f9dd',
    };

    useEffect(() => {
        (async () => {
            const res = await getInfo();
            if (res) {
                setName(res.name);
                setBeanState(res.status);
                setSearchToken(res.webSearch?.token);
            }
        })();
    }, []);

    const content = useMemo(() => {
        if (beanState === BeanState.created) {
            return (
                [{
                    title: locales.addDocs,
                    children: <ImportDocs />,
                    key: 'docs'
                }]
            );
        }
        return (
            [
                {
                    title: locales.addDocs,
                    children: <ImportDocs />,
                    key: 'docs'
                },
                {
                    title: locales.addExamples,
                    children: <Example />,
                    key: 'examples'
                },
                {
                    title: locales.accessWeChat,
                    children: (
                        <div className={styles.btn}>
                            {locales.viewDetail}
                            <IconFont icon="icon-GotoOutline" />
                        </div>
                    ),
                    key: 'accessWeChat'
                },
                {
                    title: locales.accessFeishu,
                    children: <IntegrateFeishu />,
                    key: 'accessFeishu'
                },
                {
                    title: locales.switchSearch,
                    children: <ToggleSearch webSearchToken={searchToken} />,
                    key: 'switchSearch'
                },
            ]
        );
    }, [locales, searchToken]);

    return (
        <div className={styles.beanDetail}>
            <div className={styles.logo}>
                <img src={logo} alt="huixiangdou" />
            </div>
            <div className={styles.statisticsItem}>
                <div className={styles.statisticsItemTitle}>
                    {locales.beanName}
                    <img className={styles.titleImg} src={bean} />
                </div>
                <div>
                    <strong>{name}</strong>
                    <span
                        className={styles.beanState}
                        style={{ background: color[beanState] }}
                    >
                        {state[beanState]}
                    </span>
                </div>
            </div>
            <div className={styles.statisticsWrapper}>
                {content.map((item) => (
                    <div
                        key={item.key}
                        className={styles.statisticsItem}
                    >
                        <div className={styles.statisticsItemTitle}>{item.title}</div>
                        <div>{item.children}</div>
                    </div>
                ))}
            </div>
            {beanState > BeanState.created && (
                <div className={styles.statisticsItem}>
                    <div className={styles.statisticsItemTitle}>{locales.chatTest}</div>
                    <div>
                        <Chat />
                    </div>
                </div>
            )}
        </div>
    );
};

export default BeanDetail;
