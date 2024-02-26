import styles from './header.module.less';

const Header = () => {
    return (
        <header className={styles.header}>
            <div className={styles.menus}>SeaLion</div>
        </header>
    );
};

export default Header;
