import { headers } from "next/headers";
import { notFound } from "next/navigation";
import { hasLocale, NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { clientMessages } from "@/i18n/client-messages";
import { routing } from "@/i18n/routing";
import { fontVariables } from "../fonts";
import "../globals.css";

export function generateStaticParams() {
  return routing.locales.map((locale) => ({ locale }));
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  if (!hasLocale(routing.locales, locale)) notFound();
  setRequestLocale(locale);
  // Reading request headers opts every page into dynamic rendering, which the
  // per-request CSP nonce requires (Next stamps its inline scripts with it).
  await headers();
  // Client components get the catalogue minus the verdict/health namespaces.
  const messages = clientMessages(await getMessages());
  return (
    <html lang={locale} className={fontVariables}>
      <body className="min-h-dvh bg-surface-canvas font-sans text-text-primary antialiased">
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
