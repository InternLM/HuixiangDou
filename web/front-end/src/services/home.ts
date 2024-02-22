import { request } from '@/utils/ajax';

const beanPrefix = '';

export enum MsgCode {
    success = '10000',
    notAuthed = 'A1000',
    createFail = 'A2000',
    loginFail = 'A2001',
    notExist = 'A2002',
}

export interface BeanRspDto {
    'exist': boolean,
    'featureStoreId': string // 知识库id
}
export interface BeanInfoDto {
    'featureStoreId': string,
    'docs': string[],
    'status': number,
    'suffix': string,
    'feishu': {
        'webhookUrl': string,
        'appId': string,
        'appSecret': string,
        'encryptKey': string,
        'verificationToken': string,
        'eventUrl': string
    },
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

export async function loginBean(name: string, password: string) {
    return request<BeanRspDto>('/api/v1/access/v1/login', {
        method: 'POST',
        data: {
            name,
            password
        }
    }, beanPrefix);
}

export async function getInfo(featureStoreId: string) {
    return request<BeanInfoDto>('/api/v1/qalib/v1/getInfo', {
        method: 'POST',
        data: {
            featureStoreId
        }
    }, beanPrefix);
}

export async function addDocs(files: string[]) {
    return request<>('/api/v1/qalib/v1/addDocs', {
        method: 'POST',
        headers: {
            'Content-Type': 'multipart/form-data'
        },
        // upload files by form-data
        data: files
    }, beanPrefix);
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
