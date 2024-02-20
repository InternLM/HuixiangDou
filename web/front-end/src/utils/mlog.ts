import { MeasurementId, openLog } from '@config/log';

declare global {
    interface Window {
        dataLayer: any;
        mlog: any;
    }
}

window.mlog = null;

export const ScriptUrl = `https://www.googletagmanager.com/gtag/js?id=${MeasurementId}`;

class Mlog {
    log: ((...params: any[]) => void) | undefined;

    static init(): Promise<string | null> {
        if (!openLog) return Promise.resolve(null);

        return new Promise((resolve, reject) => {
            if (window.mlog && window.mlog instanceof Mlog) {
                resolve(null);
                return;
            }

            const syncScript = document.createElement('script');
            syncScript.innerHTML = `
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${MeasurementId}');
            `;

            document.head.append(syncScript);
            const statisScript = document.createElement('script');
            statisScript.async = true;
            statisScript.src = ScriptUrl;
            statisScript.onload = () => {
                resolve(null);
            };

            statisScript.onerror = () => {
                reject('load failed');
            };
            document.head.insertBefore(statisScript, syncScript);
            window.mlog = new Mlog();
        });
    }

    static configUserId(userId) {
        if (!openLog) return;
        if (typeof window.gtag === 'function') {
            window.gtag('config', MeasurementId, {
                user_id: userId
            });
        }
    }

    static sendEvent(eventName: string, ext: any): void {
        if (!openLog) return;

        if (typeof window.gtag === 'function') {
            window.gtag('event', eventName, ext);
        }
    }
}

export default Mlog;
