import { FC, ReactNode, HTMLAttributes } from 'react';
import classNames from 'classnames';
import styles from './button.module.less';

export interface ExampleProps extends HTMLAttributes<HTMLDivElement> {
    disabled?: boolean;
    onClick?: () => void;
    children?: ReactNode;
    className?: string;
}

const Button: FC<ExampleProps> = ({
    disabled = false,
    onClick, children,
    className,
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
            className={classNames(className, styles.btn)}
            onClick={handleClick}
        >
            {children}
        </div>
    );
};

export default Button;
