// 接口请求相关的配置信息

// 各个环境的接口请求域名
export const ApiBaseUrlMap = {
    development: '',
    staging: '',
    production: ''
};

// 各个环境的接口前缀
export const ApiPrefixMap = {
    mock: '',
    development: '',
    staging: '',
    production: ''
};

export const Env = import.meta.env.VITE_NODE;

export const BaseURL = ApiBaseUrlMap[Env];

export const ApiPrefix = ApiPrefixMap[Env];
