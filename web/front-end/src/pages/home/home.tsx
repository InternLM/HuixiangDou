import { useNavigate } from 'react-router-dom';
import { useLocale } from '@hooks/useLocale';
import { Input, message } from 'sea-lion-ui';
import { useState } from 'react';
import logo from '@assets/imgs/logo.png';
import styles from './home.module.less';

const Home = () => {
    const navigate = useNavigate();
    const [beanName, setBeanName] = useState('');
    const [beanPwd, setBeanPwd] = useState('');
    const [existed, setExisted] = useState(false);
    const locales = useLocale('home');

    const resetInput = () => {
        setBeanName('');
        setBeanPwd('');
    };

    const validateBean = (name, passward) => {
        return true;
    };

    const handleConfirm = () => {
        if (beanName && beanPwd) {
            if (validateBean(beanName, beanPwd)) {
                navigate('/demo');
            } else if (!existed) {
                setExisted(false);
            } else {
                message.error(locales.pwdError);
            }
        }
    };

    const Statistics = [
        {
            title: locales.bean,
            key: 'bean',
            number: 769
        },
        {
            title: locales.WeChat,
            key: 'WeChat',
            number: '1,099'
        },
        {
            title: locales.users,
            key: 'users',
            number: '29,648'
        },
        {
            title: locales.activeBean,
            key: 'activeBean',
            number: 218
        },
        {
            title: locales.feishu,
            key: 'feishu',
            number: 791
        },
        {
            title: locales.uniqueUsers,
            key: 'uniqueUsers',
            number: '19,825'
        }
    ];
    return (
        <div className={styles.home}>
            <div className={styles.wrapper}>
                <div className={styles.logo}>
                    <img src={logo} alt="huixiangdou" />
                </div>
                <div className={styles.inputWrapper}>
                    <Input
                        placeholder={locales.beanName}
                        value={beanName}
                        onChange={(e) => setBeanName(e.target.value)}
                    />
                    <Input
                        placeholder={locales.beanPwd}
                        value={beanPwd}
                        onChange={(e) => setBeanPwd(e.target.value)}
                    />
                </div>
                <div className={styles.btnWrapper}>
                    <div
                        className={styles.cancelBtn}
                        onClick={resetInput}
                    >
                        {locales.cancel}
                    </div>
                    <div
                        className={styles.btn}
                        onClick={handleConfirm}
                        aria-disabled={!beanName || !beanPwd}
                    >
                        {existed ? locales.create : locales.go}
                    </div>
                </div>
                <div className={styles.divider} />
                <div className={styles.statisticsWrapper}>
                    {Statistics.map((item) => (
                        <div
                            key={item.key}
                            className={styles.statisticsItem}
                        >
                            <div className={styles.statisticsItemTitle}>{item.title}</div>
                            <div className={styles.statisticsItemNumber}>{item.number}</div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default Home;
