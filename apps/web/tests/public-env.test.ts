import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

// Every NEXT_PUBLIC_* name the web app reads must be on the root AGENTS.md
// allow-list (rule 5), be a Docker build ARG, and be passed by the dev deploy
// and `just docker-web` (cleanup c7: NEXT_PUBLIC_FEATURE_VOICE was missing).

const ROOT = join(process.cwd(), "../..");
const read = (p: string) => readFileSync(join(ROOT, p), "utf8");

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? files(p) : [p];
  });
}

const used = [
  ...new Set(
    files(join(process.cwd(), "src"))
      .filter((f) => /\.(ts|tsx)$/.test(f))
      .flatMap(
        (f) => readFileSync(f, "utf8").match(/NEXT_PUBLIC_[A-Z_]+/g) ?? [],
      ),
  ),
].sort();

describe("public env names", () => {
  it("finds the names the app reads", () => {
    expect(used).toContain("NEXT_PUBLIC_FEATURE_VOICE");
  });

  it.each(used)(
    "%s is allow-listed, a build ARG and passed by every build",
    (name) => {
      const agents = read("AGENTS.md");
      const allowList = agents.slice(
        agents.indexOf("The web app exposes only"),
        agents.indexOf("Nothing secret is ever named"),
      );
      expect(allowList).toContain(`\`${name}\``);
      expect(read("apps/web/Dockerfile")).toMatch(
        new RegExp(`^ARG ${name}\\b`, "m"),
      );
      expect(read(".github/workflows/deploy-dev.yml")).toContain(
        `--build-arg ${name}=`,
      );
      expect(read("justfile")).toContain(`--build-arg ${name}=`);
      expect(read("apps/web/.env.example")).toMatch(
        new RegExp(`^${name}=`, "m"),
      );
    },
  );

  it("voice is off by default everywhere", () => {
    expect(read("apps/web/Dockerfile")).toContain(
      "ARG NEXT_PUBLIC_FEATURE_VOICE=false",
    );
    expect(read(".github/workflows/deploy-dev.yml")).toContain(
      "NEXT_PUBLIC_FEATURE_VOICE: " +
        "$" +
        "{{ vars.NEXT_PUBLIC_FEATURE_VOICE || 'false' }}",
    );
    expect(read("justfile")).toContain(
      '--build-arg NEXT_PUBLIC_FEATURE_VOICE="' +
        "$" +
        '{NEXT_PUBLIC_FEATURE_VOICE:-false}"',
    );
    const android = JSON.parse(read("apps/app/env/example.json"));
    expect(android.FEATURE_VOICE).toBe("false");
    expect(android).toHaveProperty("SITE_URL");
  });
});
