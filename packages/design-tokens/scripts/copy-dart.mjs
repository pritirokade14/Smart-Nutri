import { copyFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";

const src = new URL("../build/dart/tokens.dart", import.meta.url);
const destDir = new URL("../../../apps/app/lib/core/theme/", import.meta.url);
mkdirSync(destDir, { recursive: true });
copyFileSync(src, fileURLToPath(new URL("tokens.g.dart", destDir)));
