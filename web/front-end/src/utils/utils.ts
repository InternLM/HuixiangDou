import { useIntl } from 'react-intl';
import qs from 'query-string';
import jsCookie from 'js-cookie';
import { clientId, logURL, TokenCookieDomain } from '@config/auth';
import { fetchCurrentUser as queryCurrentUser } from '@services/user';

export type Language = 'zh-CN' | 'en-US';
export const LanguageKey = 'locale';

export const loadLang = () => {
    const storeLang = window.localStorage.getItem(LanguageKey);
    if (storeLang) {
        return storeLang === 'en-US' ? 'en-US' : 'zh-CN';
    }
    // auto detect system language
    const systemLang = window.navigator.language;
    if (systemLang.includes('zh')) {
        localStorage.setItem(LanguageKey, 'zh-CN');
        return 'zh-CN';
    }
    // default lang: English
    localStorage.setItem(LanguageKey, 'en-US');
    return 'en-US';
};

let currentLang: Language = loadLang();
const saveLang = (lang: Language) => {
    window.localStorage.setItem(LanguageKey, lang);
    return lang;
};

export const getLang = () => currentLang;
export const setLang = (lang: Language) => {
    currentLang = saveLang(lang);
};

export const Intl = (id: string) => {
    return useIntl().formatMessage({ id });
};

// 用javascript删除某一个cookie的方法，该方法传入要删除cookie的名称
export const removeCookie = (cookieName: string) => {
    const cookies = document.cookie.split(';');// 将所有cookie键值对通过分号分割为数组
    // 循环遍历所有cookie键值对
    for (let i = 0; i < cookies.length; i++) {
        // 有些cookie键值对前面会莫名其妙产生一个空格，将空格去掉
        const _cookieName = cookies[i].split('=')[0].trim();
        // 比较每个cookie的名称，找到要删除的那个cookie键值对
        if (_cookieName === cookieName) {
            const exp = new Date();// 获取客户端本地当前系统时间

            // 将exp设置为客户端本地时间1分钟以前，将exp赋值给cookie作为过期时间后，就表示该cookie已经过期了, 那么浏览器就会将其立刻删除掉
            exp.setTime(exp.getTime() - 60);

            // 设置要删除的cookie的过期时间，即在该cookie的键值对后面再添加一个expires键值对
            // 并将上面的exp赋给expires作为值(注意expires的值必须为UTC或者GMT时间，不能用本地时间）
            // 那么浏览器就会将该cookie立刻删除掉
            document.cookie = `${cookies[i]};expires=${exp.toUTCString()};path=/;domain=${TokenCookieDomain}`;

            // 注意document.cookie的用法很巧妙，在对其进行赋值的时候是设置单个cookie的信息，但是获取document.cookie的值的时候是返回所有cookie的信息
            break;// 要删除的cookie已经在客户端被删除掉，跳出循环
        }
    }
};

export const formatQuery = (basename = '') => {
    const { search, pathname } = window.location;
    const url: string = pathname + search;
    let oauthCode;
    let realPath = '';
    const query = qs.parse(search) || {};
    const code = query.code || '';
    const lang = query.lang || '';
    if (url.startsWith(basename)) {
        // 判断 pathname 是否是以 basename 开头
        realPath = url.slice(basename?.length);
        realPath = realPath.startsWith('/') ? realPath : `/${realPath}`;
    }
    // 从 uaa 鉴权成功后，会把 code 拼在 url 最后
    // 兼容 子平台中用 code 作为业务参数
    if (Array.isArray(code)) {
        oauthCode = code[code.length - 1] || '';
    } else {
        oauthCode = code;
    }
    // 除了 code 外 url 还有其他的 query ，或者 有多个 code 的情况下
    // 鉴权 code 一定在 url 最后
    if (Object.keys(query).length > 1 || Array.isArray(code)) {
        realPath = realPath.replace(`&code=${oauthCode}`, '');
    } else {
        // url 只有 code 一个 query
        realPath = realPath.replace(`?code=${oauthCode}`, '');
    }

    realPath = realPath.replace(`?lang=${lang}&`, '?');
    realPath = realPath.replace(`?lang=${lang}`, '');
    realPath = realPath.replace(`&lang=${lang}`, '');

    return {
        realPath,
        oauthCode,
        lang,
    };
};

export const Token = {
    tokenKey: 'hxd_token',
    cookieTokenKey: 'hxd_token',
    getFromCookie() {
        return jsCookie.get(this.cookieTokenKey);
    },

    storage(token: string | null | undefined) {
        if (token === undefined || token === null) {
            // localStorage.removeItem(this.tokenKey);
            console.log(`[Token]: ${token} is invalidate`);
            return false;
        }
        localStorage.setItem(this.tokenKey, token);
        return true;
    },

    update(token: string | null) {
        const oldToken = localStorage.getItem(this.tokenKey);
        if (oldToken !== token) {
            this.storage(token);
        }
    },

    get() {
        const currentToken = this.getFromCookie() as (string | null);

        this.update(currentToken);
        return currentToken || localStorage.getItem(this.tokenKey);
    },

    has() {
        return !!this.get();
    },

    removeAll() {
        removeCookie(this.cookieTokenKey);
        removeCookie('ssouid');
        localStorage.removeItem(this.tokenKey);
    }
};

export const UserInfo = {
    key: '_$_userinfo_key_$_',

    async get(token: string) {
        const userInfo = localStorage.getItem(this.key);
        if (userInfo) return JSON.parse(userInfo);

        if (token && !userInfo) {
            const resp = await queryCurrentUser(token);
            localStorage.setItem(this.key, JSON.stringify(resp));
            return resp;
        }

        return null;
    },

    del() {
        localStorage.removeItem(this.key);
    }
};

// Function which concat all functions together
export const callFnsInSequence = (...fns: any[]) => (...args: any) => fns.forEach((fn) => fn && fn(...args));

export const jumpLogin = () => {
    let href = window.location.href;
    const url = new URL(href);

    if (url.searchParams.has('code')) {
        url.searchParams.delete('code');

        if (url.searchParams.has('lang')) url.searchParams.delete('lang');

        href = url.toString();
    }
    // debugger;
    return `${logURL}/authentication?redirect=${href}&clientId=${clientId}&lang=${getLang()}`;
};

export const isNeedAuth = (authPages): boolean => {
    const pathname = window.location.pathname.endsWith('/') ? window.location.pathname.slice(0, -1) : window.location.pathname;
    const matchPage = authPages.find(page => new RegExp(page).test(pathname));
    return !!matchPage;
};
