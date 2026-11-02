// Minimal stand-in for the API (server-side fetches can't be mocked by page.route).
import { createServer } from "node:http";

const port = Number(process.env.STUB_API_PORT ?? 8000);

const body = {
  product: {
    attribution: "openfoodfacts",
    barcode: "8901063201089",
    brand: "Parle",
    category: "biscuit",
    claims: [],
    image_url: "https://images.openfoodfacts.org/images/products/x/front.jpg",
    ingredients: ["wheat flour", "sugar"],
    name: "Parle-G",
    per_100g: {},
    product_id: null,
    serving_size_g: null,
    source: "openfoodfacts",
  },
  report: {
    nutriscore: { grade: "D" },
    high_in: ["sugar"],
    claims: [],
  },
  score_label: "calculated_by_smartnutri",
};

createServer((req, res) => {
  if (req.url === "/health") {
    res.writeHead(200).end("ok");
    return;
  }
  const ok = req.url?.startsWith("/v1/products/8901063201089/public");
  res.writeHead(ok ? 200 : 404, { "content-type": "application/json" });
  res.end(
    JSON.stringify(
      ok
        ? body
        : {
            error: { code: "product_not_found", message_key: "x", details: {} },
          },
    ),
  );
}).listen(port, "127.0.0.1");
