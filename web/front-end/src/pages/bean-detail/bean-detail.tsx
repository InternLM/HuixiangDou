import {
    FC, ReactNode, useEffect, useState
} from 'react';
import { useLocale } from '@hooks/useLocale';
import { useParams } from 'react-router-dom';
import { IconFont, Switch } from 'sea-lion-ui';
import logo from '@assets/imgs/logo.png';
import bean from '@assets/imgs/bean.png';
import Chat from '@pages/bean-detail/components/chat';
import classNames from 'classnames';
import { getInfo } from '@services/home';
import ToggleSearch from '@pages/bean-detail/components/toggle-search';
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
    const beanId = decodeURI(useParams()?.beanName);
    const [beanState, setBeanState] = useState(BeanState.created);

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

    const content = [
        {
            title: locales.addDocs,
            children: (
                <div className={styles.btn}>
                    {locales.docs}
                    <IconFont icon="icon-DocOutlined" />
                </div>
            ),
            key: 'docs'
        },
        {
            title: locales.addExamples,
            children: (
                <div className={styles.btn}>
                    {locales.viewAndEdit}
                    <IconFont icon="icon-FeedbackOutlined" />
                </div>
            ),
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
            children: (
                <div className={styles.btn}>
                    {locales.viewDetail}
                    <IconFont icon="icon-GotoOutline" />
                </div>
            ),
            key: 'accessFeishu'
        },
        {
            title: locales.switchSearch,
            children: <ToggleSearch />,
            key: 'switchSearch'
        },
    ];

    useEffect(() => {
        (async () => {
            const res = await getInfo(beanId);
            if (res) {
                setBeanState(res.status);
            }
        })();
    }, [beanId]);

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
                    <strong>{beanId}</strong>
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
            <div className={styles.statisticsItem}>
                <div className={styles.statisticsItemTitle}>{locales.chatTest}</div>
                <div>
                    <Chat />
                </div>
            </div>
        </div>
    );
};

export default BeanDetail;
