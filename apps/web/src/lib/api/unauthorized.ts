export type UnauthorizedDeps = {
  locale: string;
  signOut: () => Promise<unknown>;
  currentPath: () => string;
  navigate: (url: string) => void;
};

/** Sign out in the browser, then go to sign-in carrying the current path. */
export async function handleUnauthorized(d: UnauthorizedDeps): Promise<void> {
  try {
    await d.signOut();
  } catch {
    // Still leave the page: the token is already rejected.
  }
  const next = encodeURIComponent(d.currentPath());
  d.navigate(`/${d.locale}/sign-in?next=${next}`);
}
