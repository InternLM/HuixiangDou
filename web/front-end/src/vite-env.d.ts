/// <reference types="vite/client" />

// declare Google Analytics gtag.js
declare interface Window {gtag: any; dataBuried: any; sealionJSONPCallback: any; }

interface ImportMetaEnv {
    readonly VITE_NODE: string
    // 更多环境变量...
}

interface ImportMeta {
    readonly env: ImportMetaEnv
}

