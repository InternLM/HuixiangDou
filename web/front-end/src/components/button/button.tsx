import { FC, ReactNode, HTMLAttributes } from 'react';
import styles from './button.module.less';

export interface ExampleProps extends HTMLAttributes<HTMLDivElement> {
    onClick?: () => void;
    children?: ReactNode;
}

const Button: FC<ExampleProps> = ({ onClick, children }) => {
    return (
        <div className={styles.btn} onClick={onClick}>
            {children}
        </div>
    );
};

export default Button;
