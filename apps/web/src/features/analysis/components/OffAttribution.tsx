import { useTranslations } from "next-intl";

/** ODbL credit for Open Food Facts data, linked to the product's OFF page. */
export function OffAttribution({ barcode }: { barcode: string | null }) {
  const t = useTranslations();
  return (
    <p className="text-(length:--text-sm)">
      {barcode ? (
        <a
          href={`https://world.openfoodfacts.org/product/${encodeURIComponent(barcode)}`}
          rel="noopener noreferrer"
          className="underline"
        >
          {t("attribution.off")}
        </a>
      ) : (
        t("attribution.off")
      )}
    </p>
  );
}
