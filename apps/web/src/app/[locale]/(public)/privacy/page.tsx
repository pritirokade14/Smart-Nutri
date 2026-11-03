import type { Metadata } from "next";
import {
  LegalPage,
  legalMetadata,
} from "@/features/legal/components/LegalPage";

type Params = Promise<{ locale: string }>;

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  return legalMetadata("privacy", (await params).locale);
}

// Public but noindex until lawyer sign-off (proxy PUBLIC): the policy text only.
export default async function PrivacyPage({ params }: { params: Params }) {
  return <LegalPage kind="privacy" locale={(await params).locale} />;
}
