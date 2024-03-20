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
    feishu: Feishu;
    refresh: () => void;
    children?: ReactNode;
}

const IntegrateFeishu: FC<IntegrateFeishuProps> = ({
    feishu,
    refresh,
    children
}) => {
    const [form] = Form.useForm();
    const locales = useLocale('beanDetail');

    const [openModal, setOpenModal] = useState(false);
    const [eventUrl, setEventUrl] = useState(feishu?.eventUrl);
    const [loading, setLoading] = useState(false);

    const handleOpen = () => {
        setOpenModal(true);
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
            {eventUrl ? (
                <div
                    className={styles.webhookUrl}
                    onClick={handleOpen}
                    title={locales.edit}
                >
                    {eventUrl}
                </div>
            ) : (
                <Button onClick={handleOpen}>
                    {locales.viewDetail}
                    <IconFont icon="icon-IntroductionOutlined" />
                </Button>
            )}
            <Modal
                open={openModal}
                title={locales.integrateLark}
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <div>{locales.larkGuidance}</div>
                <div className={styles.eventurl}>eventUrl: </div>
                {eventUrl && (
                    <CopyCode code={eventUrl} />
                )}
                <Form
                    form={form}
                    layout="vertical"
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
                <Button onClick={handleSubmit}>
                    {
                        loading ? locales.saving : locales.save
                    }
                </Button>
            </Modal>
        </div>
    );
};

export default IntegrateFeishu;
