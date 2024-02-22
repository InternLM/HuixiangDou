import { FC, ReactNode, useState } from 'react';
import {
    Input, message, Modal, Switch
} from 'sea-lion-ui';
import Button from '@components/button/button';
import { useParams } from 'react-router-dom';
import { integrateWebSearch } from '@services/home';
import styles from './toggle-search.module.less';

export interface ToggleSearchProps {
    webSearchToken: string;
    children?: ReactNode;
}

const ToggleSearch: FC<ToggleSearchProps> = ({ webSearchToken, children }) => {
    const beanId = decodeURI(useParams()?.beanName);

    const [openModal, setOpenModal] = useState(false);
    const [token, setToken] = useState('');

    const handleOpen = () => {
        setOpenModal(true);
    };

    const handleSaveToken = async () => {
        if (!token) {
            message.error('token不能为空');
            return;
        }
        const res = await integrateWebSearch(beanId, token);
    };

    return (
        <div className={styles.toggleSearch}>
            <div
                className={styles.token}
                onClick={handleOpen}
                title="点击修改"
            >
                {webSearchToken || '尚未开启网络搜索'}
            </div>
            <Modal
                open={openModal}
                title="网络搜索"
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <div>开启网络搜索，知识助手可以综合网络结果和本地文档给出答复</div>
                <div>1. 注册 Serper  获取限量免费 token</div>
                <div>2. 填入 token, 新 token 会覆盖旧 token </div>
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
