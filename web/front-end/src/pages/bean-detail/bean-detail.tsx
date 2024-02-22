import { FC, ReactNode, useState } from 'react';
import { useLocale } from '@hooks/useLocale';
import { useParams } from 'react-router-dom';
import { IconFont, Switch } from 'sea-lion-ui';
import logo from '@assets/imgs/logo.png';
import bean from '@assets/imgs/bean.png';
import Chat from '@pages/bean-detail/components/chat';
import classNames from 'classnames';
import styles from './bean-detail.module.less';

export interface BeanDetailProps {
    children?: ReactNode;
}

export enum BeanState {
    'failed' = -1,
    'normal' = 0,
    'exception' = 2,
}

const BeanDetail: FC<BeanDetailProps> = () => {
    const locales = useLocale('beanDetail');
    const beanName = decodeURI(useParams('beanName')?.beanName);
    const [beanState, setBeanState] = useState(BeanState.failed);
    const content = [
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
            title: locales.addDocs,
            children: (
                <div className={styles.btn}>
                    {locales.viewAndEdit}
                    <IconFont icon="icon-FeedbackOutlined" />
                </div>
            ),
            key: 'docs'
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
            children: <Switch />,
            key: 'switchSearch'
        },
    ];
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
                    <strong>{beanName}</strong>
                    <span className={classNames(styles.beanState, { [styles.failState]: beanState !== 0 })}>异常</span>
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
