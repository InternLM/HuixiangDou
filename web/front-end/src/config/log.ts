// 日志相关配置

const VITE_NODE = import.meta.env.VITE_NODE;

export const openLog = false;

export const MeasurementIdMap = {
    development: 'G-KKD0ZHPWHK',
    staging: 'G-KKD0ZHPWHK',
    production: 'G-2B37EDDDC9'
};

export const MeasurementId = MeasurementIdMap[VITE_NODE];
