import {
    FC, ReactNode, useEffect, useState
} from 'react';
import {
    IconFont, Input, message, Modal
} from 'sea-lion-ui';
import { Form } from 'antd';
import {
    Feishu, integrateLark, MsgCode
} from '@services/home';
import Button from '@components/button/button';
import { useLocale } from '@hooks/useLocale';
import CopyCode from '@components/copy-code/copy-code';
import styles from './integrate-feishu.module.less';

export interface IntegrateFeishuProps {
    suffix: string;
    feishu: Feishu;
    refresh: () => void;
    children?: ReactNode;
}

const IntegrateFeishu: FC<IntegrateFeishuProps> = ({
    suffix,
    feishu,
    refresh,
    children
}) => {
    const [form] = Form.useForm();
    const locales = useLocale('beanDetail');

    const [openModal, setOpenModal] = useState(false);
    const [eventUrl, setEventUrl] = useState(feishu?.eventUrl);
    const [encryptKey, setEncryptKey] = useState(feishu?.encryptKey);
    const [verificationToken, setVerificationToken] = useState(feishu?.verificationToken);
    const [loading, setLoading] = useState(false);

    const handleOpen = () => {
        setOpenModal(true);
    };

    const closeModal = () => {
        setOpenModal(false);
    };

    const handleSubmit = async () => {
        setLoading(true);
        form.validateFields()
            .then(async (values) => {
                integrateLark(values.appId, values.appSecret)
                    .then((res) => {
                        if (res && res.msgCode === MsgCode.success) {
                            setEventUrl(res.data?.eventUrl);
                            message.success(locales.saveSuccess);
                            refresh();
                        }
                    })
                    .finally(() => {
                        setLoading(false);
                    });
            }).finally(() => {
                setLoading(false);
            });
    };

    useEffect(() => {
        if (openModal && feishu) {
            form.setFieldsValue({ ...feishu });
            setEventUrl(feishu.eventUrl || '');
        } else {
            form.resetFields();
        }
    }, [openModal, feishu]);

    return (
        <div className={styles.integrateFeishu}>
            <Button onClick={handleOpen}>
                {locales.viewDetail}
                <IconFont icon="icon-IntroductionOutlined" />
            </Button>
            <Modal
                width={600}
                open={openModal}
                title={locales.integrateLark}
                footer={(<div />)}
                onClose={closeModal}
            >
                <div className={styles.title}>{locales.credentials}</div>
                <Form
                    form={form}
                >
                    <Form.Item
                        name="appId"
                        label="appId"
                        rules={[{ required: true, message: `appId ${locales.isEmpty}` }]}
                    >
                        <Input placeholder={locales.required} />
                    </Form.Item>
                    <Form.Item
                        name="appSecret"
                        label="appSecret"
                        rules={[{ required: true, message: `appSecret ${locales.isEmpty}` }]}
                    >
                        <Input placeholder={locales.required} />
                    </Form.Item>
                </Form>
                <div className={styles.flex}>
                    <Button className={styles.cancel} onClick={() => form.resetFields()}>
                        {locales.reset}
                    </Button>
                    <Button onClick={handleSubmit}>
                        {loading ? locales.saving : locales.save}
                    </Button>
                </div>

                <div className={styles.title}>{locales.encryption}</div>
                <div className={styles.flex}>
                    <span>Encrypt Key: </span>
                    <CopyCode code={encryptKey} />
                </div>
                <div className={styles.flex}>
                    <span>Verification Token: </span>
                    <CopyCode code={verificationToken} />
                </div>

                <div className={styles.title}>{locales.suffix}</div>
                <div className={styles.flex}>
                    <span>Suffix: </span>
                    <CopyCode code={suffix} />
                </div>

                <div className={styles.title}>{locales.larkGuidance}</div>
                {eventUrl && (
                    <CopyCode code={eventUrl} />
                )}
                <div className={styles.title}>{locales.reference}</div>
                <Button
                    onClick={() => window.open('https://aicarrier.feishu.cn/docx/H1AddcFCioR1DaxJklWcLxTDnEc')}
                >
                    {locales.viewGuide}
                    <IconFont icon="icon-GotoOutline" />
                </Button>
            </Modal>
        </div>
    );
};

export default IntegrateFeishu;
