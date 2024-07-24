// https://github.com/http-party/node-http-proxy#options
const ProxyConfig = {
    '/api': {
        target: 'https://p-172_dot_31_dot_0_dot_170_colon_18443.openxlab.space',
        changeOrigin: true,
        secure: false,
        rewrite: path => {
            return path.replace('^', '');
        },
    }
};

export default ProxyConfig;
