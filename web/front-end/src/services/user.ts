import { request } from '@utils/ajax';

const userServicePrefix = '/gw/user-service';
const uaaServicePrefix = '/gw/uaa-be';

export interface fetchCurrentUserReqDto {
    avatar?: string;
    email?: string;
    expiration?: string;
    roleIds?: string[];
    nickname?: string;
    jwt?: string;
    ssoUid: string;
    username?: string;
    wechat?: string;
    wechatName?: string;
    [key: string]: any;
}

// 获取用户信息
export async function fetchCurrentUser(
    token: string,
) {
    return request<fetchCurrentUserReqDto>('/api/v1/login/getUserInfo', {
        method: 'POST',
        headers: {
            Authorization: `Bearer ${token}`
        },
    }, uaaServicePrefix);
}

export async function logout() {
    return request('/api/v1/logout/all', {
        method: 'POST',
        meta: {
            isAllResponseBody: true
        },
    }, uaaServicePrefix);
}

export interface fetchOauthCodeReqDto {
    token: string;
}

// sso第三方登录验证后，拿取用户信息
export const fetchOauthCode = (code: string | string[], redirect: string) => {
    return request<fetchOauthCodeReqDto>('/api/v1/account/oauth', {
        method: 'POST',
        data: {
            code,
            redirect
        }
    }, userServicePrefix);
};
