import { redirect } from "next/navigation";
import { Providers } from "@/app/providers";
import { AppShell } from "@/components/shell/AppShell";
import { ConsentGate } from "@/features/consent/components/ConsentGate";
import { createSupabaseServerClient } from "@/lib/supabase/server";

// Every page sits behind the consent gate (terms first, ADR 0018).
// Defence in depth: the proxy already gates these routes, but the server
// component re-checks the session so a proxy bypass cannot render the page.
export default async function AppLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const supabase = await createSupabaseServerClient();
  const { data } = await supabase.auth.getClaims();
  if (!data?.claims) redirect(`/${locale}/sign-in`);
  return (
    <Providers>
      <AppShell locale={locale}>
        <ConsentGate>{children}</ConsentGate>
      </AppShell>
    </Providers>
  );
}
