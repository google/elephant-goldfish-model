# egm.dev

Landing site for the Elephant-Goldfish Model, served at https://egm.dev from GitHub Pages.

| Light | Dark |
| --- | --- |
| ![Hero, light scheme](screenshots/hero-light.png) | ![Hero, dark scheme](screenshots/hero-dark.png) |

<details>
<summary>Full page and mobile</summary>

![Full page, light scheme](screenshots/full-light.png)

![Full page, dark scheme](screenshots/full-dark.png)

![Mobile, light scheme, 375px wide](screenshots/mobile.png)

![Mobile, dark scheme, 375px wide](screenshots/mobile-dark.png)

</details>

## Stack

- [Astro](https://astro.build) static site generator. Single page, zero client framework runtime.
- [gBreeze](https://www.npmjs.com/package/@material/web) (`@material/web` `labs/gb`) native-element styles. The page applies Material Web class names (`btn`, `icon-btn`, `list-item`, `badge`, `divider`) and imports stylesheets directly in [`src/layouts/Base.astro`](src/layouts/Base.astro).
- Self-hosted fonts: Google Sans Flex and Google Sans Code under [`src/assets/fonts/`](src/assets/fonts/) ([SIL Open Font License](https://openfontlicense.org)).

## Development

Install dependencies:

```sh
npm ci
```

Start the local development server:

```sh
npm run dev
```

The site runs at `http://localhost:4321`.

## Validation

Run static type checking and build checks before submitting changes:

```sh
npm run check    # Astro type and component diagnostics
npm run build    # Production build to dist/
npm test         # Node unit tests for analytics and consent
```

All checks must pass with zero errors and zero warnings.

## Screenshot Capture

Rebuild and capture documentation screenshots and social preview images:

```sh
npm run capture
```

This command requires a local Chromium binary. Set `CHROME_PATH` if Chromium is installed in a non-standard location. Edit [`scripts/og.html`](scripts/og.html) to modify the Open Graph card source. Run `npm run capture` after any visual change to keep screenshots in sync.

## Deployment

The GitHub Actions workflow [`.github/workflows/deploy-site.yml`](../.github/workflows/deploy-site.yml) builds and deploys the site to GitHub Pages on every push to `main` that touches `site/`. The file [`public/CNAME`](public/CNAME) configures the custom domain `egm.dev`.

## Rules & Policies

- **Theming**: Customize styles only through [`src/styles/tokens.css`](src/styles/tokens.css) and component custom properties. Do not restyle gBreeze component boxes.
- **Skill Icons**: [`src/components/SkillIcon.astro`](src/components/SkillIcon.astro) references canonical SVG icons from the plugin skills directory. Do not duplicate icon files into `public/`.
- **Privacy & Analytics**: The site collects zero telemetry by default. Google Analytics 4 and the Cookie Notification Bar load only on `egm.dev` when affirmative user consent is granted and `PUBLIC_GA_MEASUREMENT_ID` is defined. Forks and local builds make no requests to Google servers.
- **Setup Guide**: See [`../docs/getting_started.md`](../docs/getting_started.md) for full plugin setup and installation instructions.
