import { GlobalLangeContext } from '@components/global-lang';
import { useContext } from 'react';
import styles from './header.module.less';

const Header = () => {
    const { locale, setLocale } = useContext(GlobalLangeContext);
    return (
        <header className={styles.header}>
            <div className={styles.language}>
                <span
                    onClick={() => setLocale('zh-CN')}
                    className={locale === 'zh-CN' && styles.chosen}
                >
                    中
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
