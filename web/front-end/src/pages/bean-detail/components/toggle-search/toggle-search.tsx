import {
    FC, ReactNode, useEffect, useState
} from 'react';
import {
    Input, message, Modal
} from 'sea-lion-ui';
import Button from '@components/button/button';
import { integrateWebSearch, MsgCode } from '@services/home';
import { Switch } from 'antd';
import styles from './toggle-search.module.less';

export interface ToggleSearchProps {
    refresh: () => void;
    webSearchToken: string;
    children?: ReactNode;
}

const ToggleSearch: FC<ToggleSearchProps> = ({
    refresh,
    webSearchToken,
    children
}) => {
    const [openModal, setOpenModal] = useState(false);
    const [token, setToken] = useState('');

    const handleChangeSwitch = async (e) => {
        console.log('webSearchToken', !!webSearchToken);
        if (!webSearchToken) {
            setOpenModal(true);
            e.preventDefault();
            e.stopPropagation();
        } else {
            const res = await integrateWebSearch('');
            if (res.msgCode === MsgCode.success) {
                refresh();
                message.success('网络搜索已关闭');
            }
        }
    };

    const handleSaveToken = async () => {
        const res = await integrateWebSearch(token);
        if (res.msgCode === MsgCode.success && !token) {
            refresh();
            message.success('网络搜索已关闭');
        } else if (res.msgCode === MsgCode.success && token) {
            refresh();
            message.success('保存成功');
        } else if (res.msg) {
            message.error(res.msg);
        }
    };

    useEffect(() => {
        if (!openModal) {
            setToken('');
        }
    }, [openModal]);

    return (
        <div className={styles.toggleSearch}>
            <Switch checked={!!webSearchToken} onClick={handleChangeSwitch} />
            <Modal
                open={openModal}
                title="网络搜索"
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <div>开启网络搜索，知识助手可以综合网络结果和本地文档给出答复</div>
                <div>
                    1. 注册
                    {' '}
                    <a target="_blank" href="https://serper.dev/api-key" rel="noreferrer">Serper</a>
                    {' '}
                    获取限量免费 token
                </div>
                <div>2. 填入 token, 新 token 会覆盖旧 token </div>
                <div>3. 如果保存一个空 token， 网络搜索会被关闭</div>
                <div className={styles.inputWrapper}>
                    <Input
                        value={token}
                        onChange={(e) => setToken(e.target.value)}
                        placeholder="填入你的token"
                    />
                    <Button onClick={handleSaveToken}>保存</Button>
                </div>
            </Modal>
        </div>
    );
};

export default ToggleSearch;
