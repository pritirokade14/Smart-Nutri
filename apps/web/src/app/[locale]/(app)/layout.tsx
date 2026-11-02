import { redirect } from "next/navigation";
import { Providers } from "@/app/providers";
import { createSupabaseServerClient } from "@/lib/supabase/server";

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
  return <Providers>{children}</Providers>;
}
