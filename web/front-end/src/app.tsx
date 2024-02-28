import { GlobalLang } from '@components/global-lang';
import useNotification from '@components/notification/use-notification';
import RouterRoot from './routes';
import './styles/index.less';
import 'sea-lion-ui/dist/index.css';

console.log(import.meta.env.VITE_NODE);

const App = () => {
    useNotification();
    return (
        <GlobalLang>
            <RouterRoot />
        </GlobalLang>
    );
};

export default App;
