"use client";

import { useLocale, useTranslations } from "next-intl";
import { Button, buttonClass } from "@/components/ui/Button";
import { chipClass } from "@/components/ui/Chip";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { LoadingState } from "@/components/ui/Skeleton";
import { errorKey } from "@/features/members/components/ConsentDialog";
import { useRecipes } from "@/features/recipes/hooks/useRecipes";
import { useCustomFoods } from "../hooks/useCustomFoods";

/**
 * My foods: the custom foods and the recipes, each paginated by cursor, with
 * a link to edit (and delete, on the edit page). No nutrient numbers here.
 */
export function MyFoods() {
  const t = useTranslations();
  const locale = useLocale();
  const foods = useCustomFoods();
  const recipes = useRecipes();
  const failed = foods.error ?? recipes.error;
  if (!failed && (!foods.data || !recipes.data))
    return <LoadingState label={t("common.loading")} />;
  if (failed || !foods.data || !recipes.data)
    return (
      <ErrorState
        message={failed ? t(errorKey(t, failed)) : t("error.internal_error")}
        onRetry={() => {
          void foods.refetch();
          void recipes.refetch();
        }}
      />
    );
  const foodItems = foods.data.pages.flatMap((p) => p.items);
  const recipeItems = recipes.data.pages.flatMap((p) => p.items);
  return (
    <div className="space-y-6" data-testid="my-foods">
      <div className="flex flex-wrap gap-2">
        <a
          href={`/${locale}/diary/foods/new`}
          className={buttonClass({ variant: "outline" })}
        >
          {t("foods.new_food")}
        </a>
        <a
          href={`/${locale}/diary/recipes/new`}
          className={buttonClass({ variant: "outline" })}
        >
          {t("foods.new_recipe")}
        </a>
      </div>
      {foodItems.length === 0 && recipeItems.length === 0 ? (
        <EmptyState title={t("recipes.empty")} />
      ) : null}
      {foodItems.length > 0 ? (
        <section className="space-y-1" data-testid="my-foods-list">
          <h2 className="text-md font-semibold text-text-primary">
            {t("foods.kind.custom_food")}
          </h2>
          <ul className="divide-y divide-border-default">
            {foodItems.map((f) => (
              <li key={f.id}>
                <a
                  href={`/${locale}/diary/foods/${f.id}`}
                  data-testid="my-food"
                  className="flex min-h-11 flex-wrap items-center justify-between gap-2 py-2 hover:bg-surface-muted"
                >
                  <span className="text-md break-words text-text-primary">
                    {f.name}
                  </span>
                  <span className={chipClass}>{t("diary.edit")}</span>
                </a>
              </li>
            ))}
          </ul>
          {foods.hasNextPage ? (
            <Button
              variant="outline"
              size="sm"
              data-testid="foods-more"
              disabled={foods.isFetchingNextPage}
              onClick={() => void foods.fetchNextPage()}
            >
              {t("nav.more")}
            </Button>
          ) : null}
        </section>
      ) : null}
      {recipeItems.length > 0 ? (
        <section className="space-y-1" data-testid="my-recipes-list">
          <h2 className="text-md font-semibold text-text-primary">
            {t("foods.kind.recipe")}
          </h2>
          <ul className="divide-y divide-border-default">
            {recipeItems.map((r) => (
              <li key={r.id}>
                <a
                  href={`/${locale}/diary/recipes/${r.id}`}
                  data-testid="my-recipe"
                  className="flex min-h-11 flex-wrap items-center justify-between gap-2 py-2 hover:bg-surface-muted"
                >
                  <span className="text-md break-words text-text-primary">
                    {r.name}
                  </span>
                  {r.incomplete_nutrients.length > 0 ? (
                    <span className={chipClass}>{t("recipes.incomplete")}</span>
                  ) : null}
                </a>
              </li>
            ))}
          </ul>
          {recipes.hasNextPage ? (
            <Button
              variant="outline"
              size="sm"
              data-testid="recipes-more"
              disabled={recipes.isFetchingNextPage}
              onClick={() => void recipes.fetchNextPage()}
            >
              {t("nav.more")}
            </Button>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
