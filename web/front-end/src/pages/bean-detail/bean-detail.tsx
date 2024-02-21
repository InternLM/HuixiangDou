import { FC, ReactNode } from 'react';
import { useLocale } from '@hooks/useLocale';
import { useParams } from 'react-router-dom';
import styles from './bean-detail.module.less';

export interface BeanDetailProps {
    children?: ReactNode;
}

const BeanDetail: FC<BeanDetailProps> = () => {
    const locales = useLocale('beanDetail');
    const beanName = decodeURI(useParams('beanName') || '');
    const content = [
        {
            title: locales.accessWeChat,
            children: (
                <div className={styles.btn}>
                    {locales.viewDetail}
                </div>
            ),
            key: 'accessWeChat'
        },
        {
            title: locales.accessFeishu,
            children: (
                <div className={styles.btn}>
                    {locales.viewDetail}
                </div>
            ),
            key: 'accessFeishu'
        },
        {
            title: locales.switchSearch,
            children: (<div>hhh</div>),
            key: 'switchSearch'
        },
        {
            title: locales.examples,
            children: (<div>hhh</div>),
            key: 'examples'
        },
        {
            title: locales.docs,
            children: (<div>hhh</div>),
            key: 'docs'
        }
    ];
    return (
        <div className={styles.beanDetail}>
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
        </div>
    );
};

export default BeanDetail;
