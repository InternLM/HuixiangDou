// 登录相关配置信息

export const VITE_NODE = import.meta.env.VITE_NODE;

// 开启单点登录开关
export const openOSS = false;

export const ClientIdMap = {
    development: '',
    staging: '',
    production: ''
};

// 登录跳转链接
export const LogURLMap = {
    development: '',
    staging: '',
    production: ''
};

// 注意 Development环境的domain前面必须加 . 因为，本地开发环境和线上开发环境域名不同
// 如果发生反复跳转，请在浏览器中查看后端返回的cookie的domain是否有问题
export const TokenCookieDomainMap = {
    development: '',
    staging: '',
    production: ''
};

export const clientId = ClientIdMap[VITE_NODE];
export const logURL = LogURLMap[VITE_NODE];
export const TokenCookieDomain = TokenCookieDomainMap[VITE_NODE];

// 针对权限更细化的配置信息

// 需要权限验证的页面可以把对应的pathname放到这里
export const AuthPages: string[] = [
    ''
];

// 有些接口不需要token
export const NoTokenApiPaths: string[] = [
    '/account/oauth',
    '/api/v1/access/v1/login',
    '/api/v1/statistic/v1/total'
];
