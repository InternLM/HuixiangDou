// https://github.com/http-party/node-http-proxy#options
const ProxyConfig = {
    '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
        secure: false,
        rewrite: path => {
            return path.replace('^', '');
        },
    }
};

export default ProxyConfig;
