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
  return legalMetadata("terms", (await params).locale);
}

// Public and indexable (proxy PUBLIC): the terms text only.
export default async function TermsPage({ params }: { params: Params }) {
  return <LegalPage kind="terms" locale={(await params).locale} />;
}
