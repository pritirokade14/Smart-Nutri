import { headers } from "next/headers";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, getTranslations } from "next-intl/server";
import "./globals.css";

// There is no root layout (the [locale] layout owns <html>), so unmatched URLs
// render this page standalone. Reading headers() keeps it dynamic so Next can
// stamp its scripts with the request's CSP nonce.
export default async function RootNotFound() {
  await headers();
  const t = await getTranslations();
  const messages = await getMessages();
  return (
    <html lang="en">
      <body>
        <NextIntlClientProvider messages={messages}>
          <main className="mx-auto max-w-xl p-(--spacing-4)">
            <h1 className="text-(length:--text-xl)">{t("error.not_found")}</h1>
          </main>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
