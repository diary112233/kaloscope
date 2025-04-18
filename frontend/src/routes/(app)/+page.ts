// https://github.com/vite-pwa/sveltekit/issues/16
// since there's no dynamic data here, we can prerender
// it so that it gets served as a static asset in production
export const prerender = true;
