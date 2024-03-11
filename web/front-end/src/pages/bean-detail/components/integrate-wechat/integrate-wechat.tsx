import { useState } from 'react';
import { IconFont, Modal } from 'sea-lion-ui';
import Button from '@components/button/button';
import { useLocale } from '@hooks/useLocale';
import styles from './integrate-wechat.module.less';

export interface IntegrateWechatProps {
    messageUrl: string;
}

const IntegrateWechat = (props: IntegrateWechatProps) => {
    const locales = useLocale('beanDetail');

    const [openModal, setOpenModal] = useState(false);

    const handleOpen = () => {
        setOpenModal(true);
    };
    return (
        <div className={styles.integrateWechat}>
            <Button onClick={handleOpen}>
                {locales.viewDetail}
                <IconFont icon="icon-IntroductionOutlined" />
            </Button>
            <Modal
                open={openModal}
                title={locales.integrateWechat}
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <div className={styles.itemTitle}>
                    {locales.WeChatCallback}
                </div>
                <div className={styles.itemContent}>
                    {props.messageUrl || locales.noCallback}
                </div>
                <div className={styles.itemTitle}>
                    {locales.wechatGuidance}
                </div>
                <Button
                    onClick={() => window.open('https://github.com/InternLM/HuixiangDou/blob/for-openxlab/docs/zero-code-add-wechat/zero_code_add_wechat_android_zh.md')}
                >
                    {locales.viewGuide}
                    <IconFont icon="icon-GotoOutline" />
                </Button>
            </Modal>
        </div>
    );
};

export default IntegrateWechat;
