"use client";

import { useTranslations } from "next-intl";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import { useMember } from "../hooks/useMembers";
import { errorKey } from "./ConsentDialog";
import { MemberForm } from "./MemberForm";

/** Loads one member (by id) into the form. */
export function MemberEditor({ id }: { id: string }) {
  const t = useTranslations();
  const member = useMember(id);
  if (member.isPending) return <LoadingState label={t("common.loading")} />;
  if (member.isError)
    return (
      <ErrorState
        message={t(errorKey(t, member.error))}
        onRetry={
          member.error.code === "member_not_found"
            ? undefined
            : () => member.refetch()
        }
        retrying={member.isFetching}
      />
    );
  return <MemberForm member={member.data} />;
}
