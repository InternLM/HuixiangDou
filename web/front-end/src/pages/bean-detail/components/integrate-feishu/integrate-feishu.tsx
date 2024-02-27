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

    const handleOpen = () => {
        setOpenModal(true);
    };

    const handleSubmit = async () => {
        form.validateFields().then(async (values) => {
            integrateLark(values).then((res) => {
                if (res && res.msgCode === MsgCode.success) {
                    setEventUrl(res.data?.eventUrl);
                    message.success('保存成功');
                    refresh();
                }
            });
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
                    title="点击修改"
                >
                    {eventUrl}
                </div>
            ) : (
                <Button onClick={handleOpen}>
                    {locales.viewDetail}
                    <IconFont icon="icon-GotoOutline" />
                </Button>
            )}
            <Modal
                open={openModal}
                title="集成飞书"
                footer={(<div />)}
                onClose={() => setOpenModal(false)}
            >
                <div>完成下面配置后，可以在飞书群聊中跟茴香豆对话</div>
                {eventUrl && (
                    <div>{`eventUrl: ${eventUrl}`}</div>
                )}
                <Form
                    form={form}
                    layout="vertical"
                >
                    <Form.Item
                        name="webhookUrl"
                        label="webhookUrl"
                        rules={[{ required: true, message: 'webhookUrl 不能为空' }]}
                    >
                        <Input placeholder="webhookUrl (必填)" />
                    </Form.Item>
                    <Form.Item
                        name="appId"
                        label="appId"
                        rules={[{ required: true, message: 'appId 不能为空' }]}
                    >
                        <Input placeholder="appId (必填)" />
                    </Form.Item>
                    <Form.Item
                        name="appSecret"
                        label="appSecret"
                        rules={[{ required: true, message: 'appSecret 不能为空' }]}
                    >
                        <Input placeholder="appSecret (必填)" />
                    </Form.Item>
                    <Form.Item
                        name="encryptKey"
                        label="encryptKey"
                        rules={[{ required: true, message: 'encryptKey 不能为空' }]}
                    >
                        <Input placeholder="encryptKey (必填)" />
                    </Form.Item>
                    <Form.Item
                        name="verificationToken"
                        label="verificationToken"
                        rules={[{ required: true, message: 'verificationToken 不能为空' }]}
                    >
                        <Input placeholder="verificationToken (必填)" />
                    </Form.Item>
                </Form>
                <Button onClick={handleSubmit}>提交</Button>
            </Modal>
        </div>
    );
};

export default IntegrateFeishu;
