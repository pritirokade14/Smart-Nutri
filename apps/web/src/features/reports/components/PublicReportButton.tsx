"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";
import { ReportButton } from "./ReportDialog";

/**
 * The F14 report button for the public product page, which has no query
 * provider of its own. Reporting needs a session: a signed-out visitor gets
 * the API's error text in the dialog, never a report.
 */
export function PublicReportButton({ productId }: { productId: string }) {
  const [client] = useState(
    () => new QueryClient({ defaultOptions: { mutations: { retry: false } } }),
  );
  return (
    <QueryClientProvider client={client}>
      <ReportButton productId={productId} />
    </QueryClientProvider>
  );
}
