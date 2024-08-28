import { defineConfig, splitVendorChunkPlugin } from 'vite';
import react from '@vitejs/plugin-react';
import { Plugin as PluginImportToCDN } from 'vite-plugin-cdn-import';
import legacy from '@vitejs/plugin-legacy';
import { ProxyConfig, ImportToCDNList, alias } from './scripts';
import { resolvePath } from './scripts/utils';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        legacy({
            targets: ['defaults', 'ie >= 11', 'chrome >= 52'],
            additionalLegacyPolyfills: ['regenerator-runtime/runtime'],
            renderLegacyChunks: true,
            polyfills: [
                'es.symbol',
                'es.array.filter',
                'es.promise',
                'es.promise.finally',
                'es/map',
                'es/set',
                'es.array.for-each',
                'es.object.define-properties',
                'es.object.define-property',
                'es.object.get-own-property-descriptor',
                'es.object.get-own-property-descriptors',
                'es.object.keys',
                'es.object.to-string',
                'web.dom-collections.for-each',
                'esnext.global-this',
                'esnext.string.match-all',
            ],
        }),
        // vite-plugin-cdn-import只会在build介入，不影响dev，dev还是依赖npm安装的包
        PluginImportToCDN({
            modules: ImportToCDNList
        }),
        splitVendorChunkPlugin(),
        react({
            babel: {
                plugins: [
                    '@babel/plugin-proposal-optional-chaining', // 兼容老版本浏览器的语法解译
                ]
            }
        })
    ],
    css: {
        modules: {
            localsConvention: 'camelCase'
        },
        preprocessorOptions: {
            less: {
                additionalData: `@import (reference) url("${resolvePath('src/styles/variables.less')}");`
            }
        }
    },
    server: {
        host: true,
        proxy: ProxyConfig
    },
    envDir: resolvePath('env'),
    resolve: {
        alias
    }
});
