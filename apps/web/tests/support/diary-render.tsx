import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import type { ReactElement } from "react";
import { clientMessages } from "@/i18n/client-messages";
import { MESSAGES, type TestLocale } from "./analyze-fixtures";

/** Renders under React Query and the locale's messages. */
export function renderIntl(ui: ReactElement, locale: TestLocale = "en") {
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <NextIntlClientProvider
        locale={locale}
        messages={clientMessages(MESSAGES[locale])}
      >
        {ui}
      </NextIntlClientProvider>
    </QueryClientProvider>,
  );
}

/** The digits left once everything marked `data-allow-digits` (dates, portions, day counts) is removed. */
export function digitsOutsideAllowed(): string[] {
  const root = document.body.cloneNode(true) as HTMLElement;
  for (const el of root.querySelectorAll("[data-allow-digits]")) el.remove();
  return (root.textContent ?? "").match(/\d/g) ?? [];
}
