import {
    FC, useCallback, useState, useMemo
} from 'react';
import { IntlProvider } from 'react-intl';
import {
    getLang, Language, setLang
} from '@utils/utils';
import locales from '@/locales';
import { GlobalLangeContext } from './global-lang-context';

const GlobalLang: FC<any> = ({ children }) => {
    const [locale, setLocale] = useState(getLang());

    const setCurrentLocale = useCallback((lang: Language) => {
        setLocale(lang);
        setLang(lang);
    }, []);

    // 子孙组件通过context获取setLocale可以更改中英文
    const value = useMemo(() => ({ locale, setLocale: setCurrentLocale }), [locale, setCurrentLocale]);

    return (
        <IntlProvider locale={locale}>
            <GlobalLangeContext.Provider value={value}>
                {children}
            </GlobalLangeContext.Provider>
        </IntlProvider>
    );
};

export default GlobalLang;
