import {
    FC, ReactNode, useEffect, useState
} from 'react';
import {
    Input, message, Modal
} from 'sea-lion-ui';
import Button from '@components/button/button';
import { integrateWebSearch, MsgCode } from '@services/home';
import { Switch } from 'antd';
import { useLocale } from '@hooks/useLocale';
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
    const locales = useLocale('beanDetail');

    const [openModal, setOpenModal] = useState(false);
    const [token, setToken] = useState('');

    const afterSuccess = () => {
        refresh();
        setOpenModal(false);
    };

    const handleChangeSwitch = async (e) => {
        if (!webSearchToken) {
            setOpenModal(true);
            e.preventDefault();
            e.stopPropagation();
        } else {
            const res = await integrateWebSearch('');
            if (res.msgCode === MsgCode.success) {
                afterSuccess();
                message.success(locales.webSearchClosed);
            }
        }
    };

    const handleSaveToken = async () => {
        const res = await integrateWebSearch(token);
        if (res.msgCode === MsgCode.success && !token) {
            afterSuccess();
            message.success(locales.webSearchClosed);
        } else if (res.msgCode === MsgCode.success && token) {
            afterSuccess();
            message.success(locales.saveSuccess);
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
                title={locales.webSearch}
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <div>{locales.webSearchDesc}</div>
                <div>
                    {`1. ${locales.register} `}
                    <a target="_blank" href="https://serper.dev/api-key" rel="noreferrer">Serper</a>
                    {' '}
                    {locales.webSearchDesc1}
                </div>
                <div>{locales.webSearchDesc2}</div>
                <div>{locales.webSearchDesc3}</div>
                <div className={styles.inputWrapper}>
                    <Input
                        value={token}
                        onChange={(e) => setToken(e.target.value)}
                        placeholder={locales.enterToken}
                    />
                    <Button onClick={handleSaveToken}>{locales.save}</Button>
                </div>
            </Modal>
        </div>
    );
};

export default ToggleSearch;
