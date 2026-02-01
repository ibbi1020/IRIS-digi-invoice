'use client';

import * as React from 'react';

export function MSWProvider({ children }: { children: React.ReactNode }) {
  const [isReady, setIsReady] = React.useState(false);

  React.useEffect(() => {
    async function initMSW() {
      if (
        typeof window !== 'undefined' &&
        process.env.NEXT_PUBLIC_ENABLE_MSW === 'true'
      ) {
        const { worker } = await import('@/mocks/browser');
        await worker.start({
          onUnhandledRequest: 'bypass',
          serviceWorker: {
            url: '/mockServiceWorker.js',
          },
        });
      }
      setIsReady(true);
    }

    initMSW();
  }, []);

  if (!isReady) {
    return null; // Or a loading spinner
  }

  return <>{children}</>;
}
