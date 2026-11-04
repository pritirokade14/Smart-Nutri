import { useLocale } from "next-intl";
import { NotFoundView } from "@/components/shell/NotFoundView";

export default function NotFound() {
  return <NotFoundView locale={useLocale()} />;
}
