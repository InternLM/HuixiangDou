// 日志相关配置

const VITE_NODE = import.meta.env.VITE_NODE;

export const openLog = false;

export const MeasurementIdMap = {
    development: '',
    staging: '',
    production: ''
};

export const MeasurementId = MeasurementIdMap[VITE_NODE];
