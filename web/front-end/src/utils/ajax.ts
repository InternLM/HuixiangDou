import axios, { AxiosError } from 'axios';
import qs from 'qs';
import { BaseURL, ApiPrefix } from '@config/base-url';
import { requestInterceptors } from '@interceptors/request';
import { responsetInterceptors, responsetErrorInterceptors } from '@interceptors/response';

export const compose = (...args: any[]) => {
    const fns = args.map(arg => {
        return typeof arg === 'function' ? arg : () => arg;
    });

    return (...innerArgs: any) => {
        let index = 0;
        let result;
        result = fns.length === 0 ? innerArgs : fns[index++](...innerArgs);

        while (index < fns.length) {
            result = fns[index++](result);
        }

        return result;
    };
};

export const instance = axios.create({
    method: 'get',
    timeout: 300000,
    responseType: 'json',
    paramsSerializer: params => qs.stringify(params, { indices: false })
});

const MetaDataMap = new Map();
export interface Meta {
    isAllResponseBody?:boolean
    isIgnoreError?:boolean
    isIgnoreGatewayError?:boolean
}

const getMeta = (url) => {
    let meta:Meta = {};
    if (MetaDataMap.has(url)) {
        meta = MetaDataMap.get(url);
        MetaDataMap.delete(url);
    }
    return meta;
};

const inBuildHandleMetaResponseInterceptors = (response) => {
    return {
        ...response,
        __meta: getMeta(response.config.url)
    };
};

const inBuildHandleMetaErrorInterceptors = (error:AxiosError) => {
    const { response } = error;
    return {
        ...error,
        __meta: getMeta(response.config.url)
    };
};

responsetInterceptors.unshift(inBuildHandleMetaResponseInterceptors);
responsetErrorInterceptors.unshift(inBuildHandleMetaErrorInterceptors);

const handleRequestInterceptors = compose(...requestInterceptors);
const handleResponsetInterceptors = compose(...responsetInterceptors);
const handleResponsetErrorInterceptors = compose(...responsetErrorInterceptors);

instance.interceptors.request.use(
    handleRequestInterceptors,
    err => (Promise.reject(err))
);

instance.interceptors.response.use(handleResponsetInterceptors, handleResponsetErrorInterceptors);

export interface DefaultRespDTO<T> {
    msgCode: number;
    msg: string;
    data: T;
}

export const ajax = <T>(api, {
    method = 'GET',
    params = {}, // url query参数
    data = {}, // http body 参数
    ...rest
}): Promise<T> => {
    const url = `${BaseURL}${api}`;
    switch (method.toLowerCase()) {
    case 'get':
        return instance.get(url, { params, ...rest });
    case 'delete':
        return instance.delete(url, { params, data, ...rest });
    case 'post':
        return instance.post(url, data, { params, ...rest });
    case 'put':
        return instance.put(url, data, { params, ...rest });
    default:
        return instance.get(url, { params, ...rest });
    }
};

export const request = <T>(api: string, options: any = {}, prefix = ApiPrefix) => {
    const needPrefix = prefix || ApiPrefix;
    const fullApi = (`${needPrefix}/${api}`).replace(/\/\//g, '/');
    if (options.meta) {
        MetaDataMap.set(fullApi, options.meta);
        delete options.meta;
    }
    return ajax<T>(fullApi, options);
};

export default ajax;
