import { GlobalLangeContext } from '@components/global-lang';
import { useContext } from 'react';
import { useLocale } from '@hooks/useLocale';
import styles from './header.module.less';

const Header = () => {
    const { locale, setLocale } = useContext(GlobalLangeContext);
    const locales = useLocale('home');
    return (
        <header className={styles.header}>
            <div
                className={styles.feedback}
                onClick={() => window.open('https://github.com/InternLM/HuixiangDou/issues')}
            >
                {locales.feedback}
            </div>
            <div className={styles.language}>
                <span
                    onClick={() => setLocale('zh-CN')}
                    className={locale === 'zh-CN' && styles.chosen}
                >
                    中
                    {' '}
                </span>
                /
                <span
                    onClick={() => setLocale('en-US')}
                    className={locale === 'en-US' && styles.chosen}
                >
                    {' '}
                    EN
                </span>
            </div>
        </header>
    );
};

export default Header;
