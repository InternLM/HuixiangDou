import { request } from '@/utils/ajax';

const beanPrefix = '';

export enum MsgCode {
    success = '10000',
    notAuthed = 'A1000',
    createFail = 'A2000',
    loginFail = 'A2001',
    notExist = 'A2002',
}
export interface BasicRespDto {
    'msgCode': string
    'msg': string,
    success: boolean
}
export interface BeanRspDto extends BasicRespDto {
    data: {
        'exist': boolean,
        'featureStoreId': string // 知识库id
    }
}
export interface Feishu {
    'webhookUrl': string,
    'appId': string,
    'appSecret': string,
    'encryptKey': string,
    'verificationToken': string,
    'eventUrl': string
}
export interface BeanInfoDto {
    'featureStoreId': string,
    'name': string,
    'docs': string[],
    'docsBase': string,
    'status': number,
    'suffix': string,
    'feishu': Feishu,
    'wechat': {
        'onMessageUrl': string
    },
    'webSearch': {
        'token': string
    }
}

export interface SampleInfoDto {
    'name': string,
    'featureStoreId': string,
    'positives': string[],
    'negatives': string[]
}

export interface StatisticDto {
    'qalibTotal': number,
    'lastMonthUsed': number,
    'wechatTotal': number,
    'feishuTotal': number,
    'servedTotal': number,
    'realServedTotal': number
}
export interface DocsRspDto {
    docsBase: string;
    docs: string[]
}

export async function getStatistic() {
    return request<StatisticDto>('/api/v1/statistic/v1/total', {
        method: 'GET',
    }, beanPrefix);
}

export async function loginBean(name: string, password: string) {
    return request<BeanRspDto>('/api/v1/access/v1/login', {
        method: 'POST',
        data: {
            name,
            password
        },
        meta: {
            isAllResponseBody: true
        }
    }, beanPrefix);
}

export async function getInfo() {
    return request<BeanInfoDto>('/api/v1/qalib/v1/getInfo', {
        method: 'POST',
    }, beanPrefix);
}

export async function addDocs(file) {
    const data = new FormData();
    data.append('files', file);
    return request('/api/v1/qalib/v1/addDocs', {
        method: 'POST',
        data
    });
}

export async function updateSampleInfo(positives: string, negatives: string) {
    return request<SampleInfoDto>('/api/v1/qalib/v1/updateSampleInfo', {
        method: 'POST',
        data: {
            positives,
            negatives
        }
    }, beanPrefix);
}

export async function getSampleInfo() {
    return request<SampleInfoDto>('/api/v1/qalib/v1/getSampleInfo', {
        method: 'POST',
    }, beanPrefix);
}

export async function integrateWebSearch(webSearchToken: string) {
    return request('/api/v1/qalib/v1/integrateWebSearch', {
        method: 'POST',
        data: {
            webSearchToken
        }
    }, beanPrefix);
}

export async function integrateLark(data: Feishu) {
    return request('/api/v1/qalib/v1/integrateLark', {
        method: 'POST',
        data
    }, beanPrefix);
}
