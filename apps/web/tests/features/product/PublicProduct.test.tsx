import enMessages from "@smartnutri/i18n/messages/en.json";
import { cleanup, render, screen } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PublicProduct } from "@/features/product/components/PublicProduct";
import {
  offProduct,
  ownProduct,
  type PublicProductOut,
  publicFixtures,
} from "../../support/public-fixtures";

afterEach(cleanup);

vi.mock("next-intl/server", async () => {
  const messages = (await import("@smartnutri/i18n/messages/en.json")).default;
  const { createTranslator } = await import("next-intl");
  return {
    setRequestLocale: () => {},
    getTranslations: async () => createTranslator({ locale: "en", messages }),
  };
});
vi.mock("next/link", () => ({
  default: ({
    href,
    children,
  }: {
    href: string;
    children: React.ReactNode;
  }) => <a href={href}>{children}</a>,
}));
const notFound = vi.hoisted(() =>
  vi.fn(() => {
    throw new Error("NEXT_NOT_FOUND");
  }),
);
vi.mock("next/navigation", () => ({ notFound }));
const loadPublicProduct = vi.hoisted(() => vi.fn());
vi.mock("@/features/product/api/public-product", () => ({ loadPublicProduct }));

function view(data: PublicProductOut) {
  return render(
    <NextIntlClientProvider locale="en" messages={enMessages}>
      <PublicProduct data={data} barcode="8901063201089" />
    </NextIntlClientProvider>,
  );
}

const cases = [
  { name: "off", data: offProduct },
  { name: "own", data: ownProduct },
  ...publicFixtures(),
];

describe("PublicProduct", () => {
  it.each(cases)("renders $name without personal data", ({ data }) => {
    const { container } = view(data);
    expect(screen.getByText(/calculated by SmartNutri/i)).toBeTruthy();
    expect(screen.queryByTestId("verdict-card")).toBeNull();
    expect(container.innerHTML.toLowerCase()).not.toContain("verdict-card");
    expect(screen.getByText(enMessages.common.disclaimer)).toBeTruthy();
  });

  it("shows name, brand, grade, chips, claim check, ingredients, image", () => {
    const { container } = view(offProduct);
    expect(screen.getByRole("heading", { name: "Parle-G" })).toBeTruthy();
    expect(screen.getByText("Parle")).toBeTruthy();
    expect(screen.getByText("Nutri-Score D")).toBeTruthy();
    expect(screen.getByText("High in sugar")).toBeTruthy();
    expect(screen.getByText("High in fat")).toBeTruthy();
    expect(screen.getByText("No added sugar")).toBeTruthy();
    expect(screen.getByText("Label data contradicts this claim")).toBeTruthy();
    expect(
      screen.getByText("The ingredients include added sugar: sugar."),
    ).toBeTruthy();
    expect(screen.getByText("wheat flour, sugar, palm oil")).toBeTruthy();
    const img = container.querySelector("img");
    expect(img?.getAttribute("alt")).toBe("Parle-G");
    expect(container.querySelector("[style]")).toBeNull();
  });

  it("omits an image that is not on the Open Food Facts host", () => {
    const evil = structuredClone(offProduct);
    evil.product.image_url = "https://evil.example/x.jpg";
    const { container } = view(evil);
    expect(container.querySelector("img")).toBeNull();
  });

  it("shows OFF attribution linked to the product page", () => {
    view(offProduct);
    const link = screen.getByRole("link", {
      name: enMessages.attribution.off,
    });
    expect(link.getAttribute("href")).toBe(
      "https://world.openfoodfacts.org/product/8901063201089",
    );
    expect(link.getAttribute("rel")).toContain("noopener");
  });

  it("shows no attribution for an own product and no-data notes", () => {
    view(ownProduct);
    expect(screen.queryByText(enMessages.attribution.off)).toBeNull();
    expect(
      screen.getByText(enMessages.nutriscore.insufficient_data),
    ).toBeTruthy();
    expect(screen.getByText(enMessages.result.no_ingredients)).toBeTruthy();
  });

  it("CTA goes to sign-in with next=result", () => {
    view(offProduct);
    const cta = screen.getByRole("link", {
      name: enMessages.product.public_cta,
    });
    expect(cta.getAttribute("href")).toBe(
      "/en/sign-in?next=/en/result/8901063201089",
    );
  });
});

describe("page", () => {
  beforeEach(() => {
    notFound.mockClear();
    loadPublicProduct.mockReset();
  });
  const call = async (barcode: string, locale = "en") => {
    const { default: Page } = await import(
      "@/app/[locale]/(public)/p/[barcode]/page"
    );
    return Page({ params: Promise.resolve({ locale, barcode }) });
  };

  it("generateMetadata sets title, canonical and hreflang", async () => {
    loadPublicProduct.mockResolvedValue({ kind: "ok", data: offProduct });
    const { generateMetadata } = await import(
      "@/app/[locale]/(public)/p/[barcode]/page"
    );
    const m = await generateMetadata({
      params: Promise.resolve({ locale: "hi", barcode: "8901063201089" }),
    });
    expect(m.title).toBe("Parle-G – nutrition facts | SmartNutri");
    const alt = m.alternates;
    expect(String(alt?.canonical)).toMatch(/\/hi\/p\/8901063201089$/);
    expect(Object.keys(alt?.languages ?? {}).sort()).toEqual([
      "en",
      "hi",
      "mr",
    ]);
    expect(String(alt?.languages?.mr)).toMatch(/\/mr\/p\/8901063201089$/);
  });

  it("invalid barcode -> notFound without calling the API", async () => {
    await expect(call("abc")).rejects.toThrow("NEXT_NOT_FOUND");
    expect(loadPublicProduct).not.toHaveBeenCalled();
  });

  it("API 404 -> notFound", async () => {
    loadPublicProduct.mockResolvedValue({ kind: "not_found" });
    await expect(call("8901063201089")).rejects.toThrow("NEXT_NOT_FOUND");
  });

  it("OFF unavailable -> retry message, no error text", async () => {
    loadPublicProduct.mockResolvedValue({ kind: "unavailable" });
    const ui = await call("8901063201089");
    render(
      <NextIntlClientProvider locale="en" messages={enMessages}>
        {ui}
      </NextIntlClientProvider>,
    );
    expect(screen.getByText(enMessages.scan.off_unavailable)).toBeTruthy();
    const retry = screen.getByRole("link", { name: enMessages.scan.retry });
    expect(retry.getAttribute("href")).toBe("/en/p/8901063201089");
  });
});
