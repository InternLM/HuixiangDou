// https://github.com/http-party/node-http-proxy#options
const ProxyConfig = {
    '/api': {
        target: 'http://10.1.52.13:7860',
        changeOrigin: true,
        secure: false,
        rewrite: path => {
            return path.replace('^', '');
        },
    }
};

export default ProxyConfig;
