import { FC, ReactNode, HTMLAttributes } from 'react';
import styles from './button.module.less';

export interface ExampleProps extends HTMLAttributes<HTMLDivElement> {
    disabled?: boolean;
    onClick?: () => void;
    children?: ReactNode;
}

const Button: FC<ExampleProps> = ({
    disabled = false,
    onClick, children
}) => {
    const handleClick = () => {
        if (disabled) {
            return;
        }
        onClick();
    };
    return (
        <div
            aria-disabled={disabled}
            className={styles.btn}
            onClick={handleClick}
        >
            {children}
        </div>
    );
};

export default Button;
