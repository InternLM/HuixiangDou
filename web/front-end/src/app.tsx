import { GlobalLang } from '@components/global-lang';
import RouterRoot from './routes';
import './styles/index.less';
import 'sea-lion-ui/dist/index.css';

console.log(import.meta.env.VITE_NODE);

const App = () => {
    return (
        <GlobalLang>
            <RouterRoot />
        </GlobalLang>
    );
};

export default App;
