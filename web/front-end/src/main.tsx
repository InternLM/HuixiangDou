import * as React from 'react';
import * as ReactDOM from 'react-dom/client';
import Mlog from '@utils/mlog';
import '@config/change-page-gray';
import App from './app';

Mlog.init();

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
    <React.StrictMode>
        <App />
    </React.StrictMode>
);
