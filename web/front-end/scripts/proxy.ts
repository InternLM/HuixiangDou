// https://github.com/http-party/node-http-proxy#options
const ProxyConfig = {
    '/mock': {
        target: 'http://localhost:3000',
        pathRewrite: {
            '^/mock': ''
        },
        secure: false // 开启https
    },
    '/api/v1': {
        target: 'http://staging.opengvlab.shlab.org.cn',
        changeOrigin: true,
    },
    '/test': {
        target: 'http://10.1.52.13:23333',
        changeOrigin: true,
        secure: false,
        rewrite: path => {
            return path.replace('^/test', '');
        },
    }
    // '/gw/app-center': {
    //     target: 'http://10.1.52.77:10019',
    //     rewrite: path => {
    //         console.log(path);
    //         return path.replace('^/gw/app-center', '');
    //     },
    //     headers: { id: '0005206' },
    //     secure: false,
    //     changeOrigin: true,
    // },
};

export default ProxyConfig;
