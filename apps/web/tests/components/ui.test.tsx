import messages from "@smartnutri/i18n/messages/en.json";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NextIntlClientProvider } from "next-intl";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Button, buttonClass } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DisclaimerFooter } from "@/components/ui/DisclaimerFooter";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { HomeIcon } from "@/components/ui/icons";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { LoadingState, Skeleton } from "@/components/ui/Skeleton";

afterEach(cleanup);

const intl = (ui: React.ReactNode) =>
  render(
    <NextIntlClientProvider locale="en" messages={messages}>
      {ui}
    </NextIntlClientProvider>,
  );

describe("Button", () => {
  it("is type=button by default and keeps a submit type when asked", () => {
    render(
      <>
        <Button>a</Button>
        <Button type="submit">b</Button>
      </>,
    );
    expect(screen.getByRole("button", { name: "a" }).getAttribute("type")).toBe(
      "button",
    );
    expect(screen.getByRole("button", { name: "b" }).getAttribute("type")).toBe(
      "submit",
    );
  });

  it("variants use brand and surface tokens, never verdict colours", () => {
    for (const variant of [
      "primary",
      "secondary",
      "outline",
      "ghost",
    ] as const) {
      const cls = buttonClass({ variant });
      expect(cls).not.toMatch(/verdict|#[0-9a-f]{3,6}/i);
    }
    expect(buttonClass()).toContain("bg-brand-primary");
    expect(buttonClass({ block: true })).toContain("w-full");
    expect(buttonClass({ size: "lg" })).toContain("min-h-12");
  });

  it("forwards click and disabled", async () => {
    const onClick = vi.fn();
    render(
      <Button onClick={onClick} disabled>
        x
      </Button>,
    );
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).not.toHaveBeenCalled();
  });
});

describe("Card and SectionHeader", () => {
  it("card renders the chosen element", () => {
    render(
      <Card as="section" aria-label="c">
        body
      </Card>,
    );
    expect(screen.getByRole("region", { name: "c" }).textContent).toBe("body");
  });

  it("section header renders a heading of the chosen level with description and action", () => {
    render(
      <SectionHeader
        as="h1"
        title="T"
        description="D"
        action={<a href="/x">A</a>}
      />,
    );
    expect(screen.getByRole("heading", { level: 1, name: "T" })).toBeTruthy();
    expect(screen.getByText("D")).toBeTruthy();
    expect(screen.getByRole("link", { name: "A" })).toBeTruthy();
  });
});

describe("EmptyState", () => {
  it("shows icon, badge, title, description and action", () => {
    render(
      <EmptyState
        icon={<HomeIcon />}
        badge="soon"
        title="Nothing yet"
        description="More later"
        action={<a href="/en/scan">go</a>}
      />,
    );
    const box = screen.getByTestId("empty-state");
    expect(box.querySelector("svg")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Nothing yet" })).toBeTruthy();
    expect(screen.getByText("soon")).toBeTruthy();
    expect(screen.getByText("More later")).toBeTruthy();
    expect(screen.getByRole("link", { name: "go" })).toBeTruthy();
  });
});

describe("ErrorState", () => {
  it("the message is the alert and retry calls back", async () => {
    const onRetry = vi.fn();
    intl(<ErrorState message="Broke" onRetry={onRetry} />);
    expect(screen.getByRole("alert").textContent).toBe("Broke");
    await userEvent.click(
      screen.getByRole("button", { name: messages.common.retry }),
    );
    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("retry is disabled while retrying; a server caller gets a retry link", () => {
    intl(<ErrorState message="m" onRetry={() => {}} retrying />);
    expect((screen.getByRole("button") as HTMLButtonElement).disabled).toBe(
      true,
    );
    cleanup();
    intl(<ErrorState message="m" retryHref="/en/p/1" retryLabel="Again" />);
    expect(
      screen.getByRole("link", { name: "Again" }).getAttribute("href"),
    ).toBe("/en/p/1");
  });

  it("no retry offered without a handler or link", () => {
    intl(<ErrorState message="m" />);
    expect(screen.queryByRole("button")).toBeNull();
    expect(screen.queryByRole("link")).toBeNull();
  });

  it("is styled neutrally (never a verdict colour)", () => {
    const { container } = intl(<ErrorState message="m" />);
    expect(container.innerHTML).not.toMatch(/verdict/);
  });
});

describe("Skeleton and LoadingState", () => {
  it("skeleton is decorative", () => {
    render(<Skeleton />);
    expect(screen.getByTestId("skeleton").getAttribute("aria-hidden")).toBe(
      "true",
    );
  });

  it("loading state announces its label", () => {
    render(<LoadingState label="Loading…" />);
    expect(screen.getByRole("status").textContent).toBe("Loading…");
    expect(screen.getAllByTestId("skeleton").length).toBeGreaterThan(1);
  });
});

describe("DisclaimerFooter", () => {
  it.each(["en", "hi", "mr"] as const)(
    "shows the disclaimer [%s]",
    async (l) => {
      const m = (await import(`@smartnutri/i18n/messages/${l}.json`)).default;
      render(
        <NextIntlClientProvider locale={l} messages={m}>
          <DisclaimerFooter />
        </NextIntlClientProvider>,
      );
      expect(screen.getByText(m.common.disclaimer)).toBeTruthy();
    },
  );
});
