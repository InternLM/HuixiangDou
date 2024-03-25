import {
    FC, ReactNode, useEffect, useMemo, useState
} from 'react';
import { useLocale } from '@hooks/useLocale';
import logo from '@assets/imgs/logo.png';
import bean from '@assets/imgs/bean1.png';
import Chat from '@pages/bean-detail/components/chat';
import { Feishu, FileState, getInfo } from '@services/home';
import ToggleSearch from '@pages/bean-detail/components/toggle-search';
import Example from '@pages/bean-detail/components/example';
import ImportDocs from '@pages/bean-detail/components/import-docs';
import IntegrateFeishu from '@pages/bean-detail/components/integrate-feishu';
import { Token } from '@utils/utils';
import { useNavigate } from 'react-router-dom';
import IntegrateWechat from '@pages/bean-detail/components/integrate-wechat/integrate-wechat';
import { Button, IconFont } from 'sea-lion-ui';
import styles from './bean-detail.module.less';

export interface BeanDetailProps {
    children?: ReactNode;
}

export enum BeanState {
    'failed' = -1,
    'created' = 0,
    'finished' = 1,
    processing = 11,
    processingError = 12,
    paramsError = 13,
    internalError = 14,
}

const BeanDetail: FC<BeanDetailProps> = () => {
    const navigate = useNavigate();
    const locales = useLocale('beanDetail');
    const [name, setName] = useState('');
    const [docs, setDocs] = useState(['']);
    const [filesState, setFilesState] = useState<FileState[]>([]);
    const [weChatInfo, setWeChatInfo] = useState(null);
    const [feishuInfo, setFeishuInfo] = useState<Feishu>(null);
    const [suffix, setSuffix] = useState('');
    const [searchToken, setSearchToken] = useState('');
    const [beanState, setBeanState] = useState(BeanState.created);
    const [refreshFlag, setRefreshFlag] = useState(false);

    const state = {
        [BeanState.failed]: locales.createFailed,
        [BeanState.created]: locales.created,
        [BeanState.finished]: locales.createSuccess,
        [BeanState.processing]: locales.processing,
        [BeanState.processingError]: locales.processingError,
        [BeanState.paramsError]: locales.paramsError,
        [BeanState.internalError]: locales.internalError,
    };
    const color = {
        [BeanState.failed]: '#f1bcbc',
        [BeanState.created]: '#ffe2bf',
        [BeanState.finished]: '#e3f9dd',
        [BeanState.processing]: '#bcdef1',
        [BeanState.processingError]: '#f1bcbc',
        [BeanState.paramsError]: '#f1bcbc',
        [BeanState.internalError]: '#f1bcbc',
    };

    const refresh = () => {
        setRefreshFlag(!refreshFlag);
    };
    const logout = () => {
        // 退出登录
        Token.removeAll();
        navigate('/home');
    };

    const getBeanInfo = async () => {
        const res = await getInfo();
        if (res) {
            setName(res.name);
            setBeanState(res.status);
            setSearchToken(res.webSearch?.token);
            setFeishuInfo(res.lark);
            setWeChatInfo(res.wechat?.onMessageUrl);
            setSuffix(res.suffix);
            if (Array.isArray(res.docs)) {
                setDocs(res.docs);
            }
            if (Array.isArray(res.filesState)) {
                setFilesState(res.filesState);
            }
        }
    };

    useEffect(() => {
        getBeanInfo();
    }, [refreshFlag]);

    // polling getInfo when beanState is created and docs is not empty
    useEffect(() => {
        let timer = null;
        if (beanState === BeanState.created && docs.length > 0) {
            timer = setInterval(() => {
                getBeanInfo();
            }, 5000);
        } else {
            clearInterval(timer);
        }
        return () => clearInterval(timer);
    }, [beanState, docs.length]);

    const content = useMemo(() => {
        if (beanState === BeanState.finished) {
            return (
                [
                    {
                        title: locales.addDocs,
                        children: <ImportDocs
                            docs={docs}
                            filesState={filesState}
                            refresh={refresh}
                        />,
                        key: 'docs'
                    },
                    {
                        title: locales.addExamples,
                        children: <Example />,
                        key: 'examples'
                    },
                    {
                        title: locales.accessWeChat,
                        children: <IntegrateWechat messageUrl={weChatInfo} />,
                        key: 'accessWeChat'
                    },
                    {
                        title: locales.accessFeishu,
                        children: <IntegrateFeishu suffix={suffix} feishu={feishuInfo} refresh={refresh} />,
                        key: 'accessFeishu'
                    },
                    {
                        title: locales.switchSearch,
                        children: <ToggleSearch refresh={refresh} webSearchToken={searchToken} />,
                        key: 'switchSearch'
                    },
                ]
            );
        }
        return (
            [{
                title: locales.addDocs,
                children: <ImportDocs filesState={filesState} refresh={refresh} />,
                key: 'docs'
            }]
        );
    }, [locales, searchToken, beanState, feishuInfo, refresh, suffix]);

    return (
        <div className={styles.beanDetail}>
            <div className={styles.logo}>
                <img src={logo} alt="huixiangdou" />
            </div>
            <div className={styles.statisticsItem}>
                <div className={styles.statisticsItemTitle}>
                    {locales.beanName}
                    <img alt="bean" className={styles.titleImg} src={bean} />
                </div>
                <div className={styles.nameWrapper}>
                    <strong>{name}</strong>
                    <span
                        className={styles.beanState}
                        style={{ background: color[beanState] }}
                    >
                        {state[beanState]}
                    </span>
                    <Button className={styles.refresh} onClick={() => window.location.reload()}>
                        {locales.refresh}
                        <IconFont icon="icon-SyncOutlined" />
                    </Button>
                    <div
                        onClick={logout}
                        className={styles.logout}
                    >
                        {locales.logout}
                    </div>
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
            {beanState === BeanState.finished && (
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
