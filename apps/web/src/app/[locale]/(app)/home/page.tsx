"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { getApi } from "@/lib/api/client";

class ApiError extends Error {
  constructor(public code: string) {
    super(code);
  }
}

async function fetchMe() {
  let result: Awaited<ReturnType<ReturnType<typeof getApi>["GET"]>>;
  try {
    result = await getApi().GET("/v1/me");
  } catch {
    throw new ApiError("network");
  }
  if (result.error || !result.data) {
    // The API envelope is { error: { code } }; the generated type only models 422.
    const code = (result.error as { error?: { code?: string } } | undefined)
      ?.error?.code;
    throw new ApiError(code ?? "internal_error");
  }
  return result.data;
}

export default function HomePage() {
  const t = useTranslations();
  const { data, error, isPending } = useQuery({
    queryKey: ["me"],
    queryFn: fetchMe,
  });

  if (isPending) return <p>{t("common.loading")}</p>;
  if (error) {
    const code = error instanceof ApiError ? error.code : "internal_error";
    return (
      <p role="alert">
        {t.has(`error.${code}`)
          ? t(`error.${code}`)
          : t("error.internal_error")}
      </p>
    );
  }
  return (
    <main className="mx-auto max-w-xl p-(--spacing-4)">
      <h1 className="text-(length:--text-xl)">
        {t("home.welcome", { name: data.display_name ?? data.email ?? "" })}
      </h1>
      <p className="text-(length:--text-sm)">{t("common.disclaimer")}</p>
    </main>
  );
}
