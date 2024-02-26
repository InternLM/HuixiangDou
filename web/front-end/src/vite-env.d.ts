/// <reference types="vite/client" />

interface ImportMetaEnv {
    readonly VITE_NODE: string
    // 更多环境变量...
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}

