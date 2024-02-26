import { useContext, useState, useEffect } from 'react';
import { GlobalLangeContext } from '@components/global-lang';
import Locale from '@/locales';

export const useLocale = (propertyName: string) => {
    const [locales, setLocales] = useState<any>({});
    const { locale: lang } = useContext(GlobalLangeContext);

    useEffect(() => {
        if (lang && Locale[lang] && Locale[lang][propertyName]) {
            setLocales(Locale[lang][propertyName]);
        }
    }, [lang, propertyName]);

    return locales;
};
