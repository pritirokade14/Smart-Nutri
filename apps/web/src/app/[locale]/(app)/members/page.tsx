import { redirect } from "next/navigation";

// The members list lives on the Family tab.
export default async function MembersPage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  redirect(`/${locale}/family`);
}
