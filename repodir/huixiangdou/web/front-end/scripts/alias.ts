import { resolvePath } from './utils';

const alias = {
    '@': resolvePath('./src'),
    '@components': resolvePath('./src/components'),
    '@layouts': resolvePath('./src/layouts'),
    '@assets': resolvePath('./src/assets'),
    '@pages': resolvePath('./src/pages'),
    '@services': resolvePath('./src/services'),
    '@utils': resolvePath('./src/utils'),
    '@styles': resolvePath('./src/styles'),
    '@routes': resolvePath('./src/routes'),
    '@config': resolvePath('./src/config'),
    '@locales': resolvePath('./src/locales'),
    '@constants': resolvePath('./src/constants'),
    '@interceptors': resolvePath('./src/interceptors'),
    '@hooks': resolvePath('./src/hooks')
};

export default alias;
