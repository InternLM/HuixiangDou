import { createPortal } from 'react-dom';

const ComponentPortal = ({ children, wrapperId = '' }) => {
    return createPortal(children, document.getElementById(wrapperId) || document.body);
};

export default ComponentPortal;
