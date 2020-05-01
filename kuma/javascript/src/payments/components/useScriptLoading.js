// @flow
import { useEffect, useState } from 'react';

/**
 * Loads the script given by the URL and cleans up after itself
 * @param string url of the script to load
 * @returns {(null | Promise)} Indicating whether the script has successfully loaded
 */
function useScriptLoading(url: string) {
    const [loadingPromise, setLoadingPromise] = useState<null | Promise<void>>(
        null
    );

    useEffect(() => {
        let script;
        if (!loadingPromise) {
            script = document.createElement('script');
            setLoadingPromise(
                new Promise((resolve, reject) => {
                    script.onload = resolve;
                    script.onerror = reject;
                })
            );
            script.src = url;

            if (document.head) {
                document.head.appendChild(script);
            }
        }
        return () => {
            if (document.head && script) {
                document.head.removeChild(script);
            }
        };
    }, [loadingPromise, url]);

    return [loadingPromise, () => setLoadingPromise(null)];
}

export default useScriptLoading;
