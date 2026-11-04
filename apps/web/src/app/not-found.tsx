import { headers } from "next/headers";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import { NotFoundView } from "@/components/shell/NotFoundView";
import { clientMessages } from "@/i18n/client-messages";
import { fontVariables } from "./fonts";
import "./globals.css";

// There is no root layout (the [locale] layout owns <html>), so unmatched URLs
// render this page standalone. Reading headers() keeps it dynamic so Next can
// stamp its scripts with the request's CSP nonce.
export default async function RootNotFound() {
  await headers();
  const locale = await getLocale();
  const messages = await getMessages();
  return (
    <html lang={locale} className={fontVariables}>
      <body className="min-h-dvh bg-surface-canvas font-sans text-text-primary antialiased">
        <NextIntlClientProvider messages={clientMessages(messages)}>
          <NotFoundView locale={locale} />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
