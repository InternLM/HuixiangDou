const MetaDataURL = 'https://openmmlab-share.oss-cn-hangzhou.aliyuncs.com/metadata/seal-lion-client-meta-data.js';

const getMetaData = (url: string): Promise<any> => {
    return new Promise((resolve, reject) => {
        let script = document.createElement('script');
        script.src = `${url}?random=${Date.now()}`;
        script.type = 'text/javascript';

        const remove = () => {
            document.body.removeChild(script);
            script = null;
        };
        window.sealionJSONPCallback = (data) => {
            resolve(data);
            remove();
        };

        script.onerror = (err) => {
            reject(err);
            remove();
        };

        document.body.appendChild(script);
    });
};

const changePageGray = ({
    open = false,
    grayscale = '100%',
    changePages = 'all',
    routerType = 'popstate'
}: {
    open?: boolean,
    grayscale?: string;
    changePages?: string[] | 'all',
    routerType?: string // 'popstate' | 'hashchange'
}) => {
    if (!open) return;

    const setPageGray = () => {
        document.body.style.cssText = `-webkit-filter: grayscale(${grayscale});-ms-filter: grayscale(${grayscale});-moz-filter: grayscale(${grayscale});filter: grayscale(${grayscale});`;
    };

    const removePageGray = () => {
        document.body.style.cssText = '';
    };

    const listenPopState = (callback) => {
        const handleChange = (changeRoute, eventType: string) => {
            if (routerType !== eventType) return;
            callback?.(changeRoute, eventType);
        };

        window.addEventListener('load', () => {
            const changeRoute = routerType === 'popstate' ? window.location.pathname : window.location.hash;
            callback(changeRoute, 'init');
        }, false);

        window.addEventListener('popstate', () => {
            handleChange(window.location.pathname, 'popstate');
        }, false);

        window.addEventListener('hashchange', () => {
            handleChange(window.location.hash, 'hashchange');
        }, false);
    };

    listenPopState((changeRoute) => {
        if (
            changePages === 'all'
            || changePages.some(p => p === changeRoute)
        ) {
            setPageGray();
        } else {
            removePageGray();
        }
    });
};

const main = async () => {
    try {
        const content = await getMetaData(MetaDataURL);
        const options = (content || {}).grayPage;
        changePageGray(options);
    } catch (error) {
        console.error(error);
    }
};

main();
