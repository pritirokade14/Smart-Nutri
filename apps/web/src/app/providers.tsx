"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useLocale } from "next-intl";
import { useEffect, useRef, useState } from "react";
import { setUnauthorizedHandler } from "@/lib/api/client";
import { handleUnauthorized } from "@/lib/api/unauthorized";
import { createSupabaseBrowserClient } from "@/lib/supabase/client";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { queries: { retry: false } } }),
  );
  const locale = useLocale();
  const handling = useRef(false);

  useEffect(
    () =>
      setUnauthorizedHandler(async () => {
        if (handling.current) return; // several calls may 401 together
        handling.current = true;
        await handleUnauthorized({
          locale,
          signOut: () => createSupabaseBrowserClient().auth.signOut(),
          currentPath: () => window.location.pathname + window.location.search,
          navigate: (url) => window.location.assign(url),
        });
      }),
    [locale],
  );

  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
