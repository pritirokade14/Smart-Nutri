"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useLocale } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { clearAnalyzeCache } from "@/features/analysis/api/useAnalyzeBarcode";
import { clearScanDrafts } from "@/features/scan/api/draftCache";
import { setUnauthorizedHandler } from "@/lib/api/client";
import { handleUnauthorized } from "@/lib/api/unauthorized";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: false } } }),
  );
  const locale = useLocale();
  const handling = useRef(false);

  // Any sign-out (explicit or forced) drops cached verdicts.
  useEffect(() => {
    const { data } = createSupabaseBrowserClient().auth.onAuthStateChange(
      (event) => {
        if (event === "SIGNED_OUT") {
          clearAnalyzeCache(client);
          clearScanDrafts(client);
        }
      },
    );
    return () => data.subscription.unsubscribe();
  }, [client]);

  useEffect(
    () =>
      setUnauthorizedHandler(async () => {
        if (handling.current) return; // several calls may 401 together
        handling.current = true;
        await handleUnauthorized({
          locale,
          clearCache: () => {
            clearAnalyzeCache(client);
            clearScanDrafts(client);
          },
          signOut: () => createSupabaseBrowserClient().auth.signOut(),
          currentPath: () => window.location.pathname + window.location.search,
          navigate: (url) => window.location.assign(url),
        });
      }),
    [locale, client],
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
