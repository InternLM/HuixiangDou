/* eslint-disable no-undef */
/* eslint-disable no-unused-vars */
declare module '*.css';
declare module '*.less';
declare module '*.png';
declare module '*.jpg';
declare module '*.jpeg';
declare module '*.svg' {
    export function ReactComponent(
        props: React.SVGProps<SVGSVGElement>,
    ): React.ReactElement;
    const url: string;
    export default url;
}
// declare Google Analytics gtag.js
declare interface Window {gtag: any; dataBuried: any; }
