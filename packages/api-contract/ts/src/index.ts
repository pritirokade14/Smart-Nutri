import createClient, { type Client } from "openapi-fetch";
import type { paths } from "./schema";

export type { components, paths } from "./schema";

export function createApiClient(
  baseUrl: string,
  getAccessToken: () => Promise<string | null>,
): Client<paths> {
  const client = createClient<paths>({ baseUrl });
  client.use({
    async onRequest({ request }) {
      const token = await getAccessToken();
      if (token) request.headers.set("Authorization", `Bearer ${token}`);
      return request;
    },
  });
  return client;
}
