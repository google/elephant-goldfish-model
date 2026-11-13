// @ts-check
import { defineConfig, fontProviders } from 'astro/config';
import starlight from '@astrojs/starlight';
import starlightLlmsTxt from 'starlight-llms-txt';
import { remarkRepositoryLinks } from './src/lib/repository-markdown.mjs';
import { unified } from '@astrojs/markdown-remark';


// Static landing site for https://egm.dev, deployed to GitHub Pages.
// Analytics and Cookie Notification Bar load only on canonical egm.dev when
// PUBLIC_GA_MEASUREMENT_ID is configured; forks and local builds make zero
// runtime requests to Google hosts.
export default defineConfig({
  site: 'https://egm.dev',
  output: 'static',
  trailingSlash: 'never',

  integrations: [starlight({
    title: 'Elephant-Goldfish Model',
    description: 'Develop ideas with context and review documents with fresh eyes.',
    favicon: '/favicon.svg',
    credits: false,
    expressiveCode: { defaultProps: { frame: 'none' }, styleOverrides: { borderRadius: '8px', borderColor: 'var(--md-sys-color-outline-variant)', codeBackground: 'var(--md-sys-color-surface-container-low)', frames: { shadowColor: 'transparent' } } },
    customCss: ['./src/styles/docs.css'],
    components: {
      Header: './src/components/docs/Header.astro',
      Head: './src/components/docs/Head.astro',
      PageTitle: './src/components/docs/PageTitle.astro',
      PageSidebar: './src/components/docs/PageSidebar.astro',
      ThemeSelect: './src/components/docs/ThemeSelect.astro',
      PageFrame: './src/components/docs/PageFrame.astro',
      Sidebar: './src/components/docs/Sidebar.astro',
      Pagination: './src/components/docs/Pagination.astro',
      MobileMenuToggle: './src/components/docs/MobileMenuToggle.astro',
    },
    sidebar: [
      { label: 'Guide', items: [
        { label: 'Overview', slug: 'guide' },
        { label: 'Install', slug: 'install' },
        { label: 'Getting started', slug: 'getting-started' },
        { label: 'Drafting and review', slug: 'workflow' },
      ] },
      { label: 'Skills', items: [
        { label: 'Overview', slug: 'skills' },
        { label: 'Brainstorm', slug: 'skills/egm-brainstorm' },
        { label: 'Draft', slug: 'skills/egm-draft' },
        { label: 'Review', slug: 'skills/egm-review' },
        { label: 'Resolve findings', slug: 'skills/egm-resolve' },
        { label: 'Custom review', slug: 'skills/egm-review-loop' },
        { label: 'Document a codebase', slug: 'skills/egm-bootstrap' },
        { label: 'Check for drift', slug: 'skills/egm-drift-report' },
        { label: 'Ask for help', slug: 'skills/egm-ask' },
      ] },
    ],
    plugins: [starlightLlmsTxt({
      details: 'The default draft and review workflow targets software designs. For other documents, configure reviewers and standards with /egm-review-loop. Humans check the findings and approve changes.',
    })],
  })],

  markdown: { processor: unified({ remarkPlugins: [remarkRepositoryLinks] }) },

  redirects: {
    '/docs': '/guide',
    '/docs/getting-started': '/getting-started',
    '/docs/workflow': '/workflow',
    '/docs/skills': '/skills',
    ...Object.fromEntries(['ask', 'bootstrap', 'brainstorm', 'draft', 'drift-report', 'resolve', 'review', 'review-loop'].map(skill => [`/docs/skills/egm-${skill}`, `/skills/egm-${skill}`])),
  },

  fonts: [
    {
      // Google Sans Flex (OFL), self-hosted so the page never calls fonts.googleapis.com.
      provider: fontProviders.local(),
      name: 'Google Sans Flex',
      cssVariable: '--font-display',
      fallbacks: ['system-ui', 'sans-serif'],
      options: {
        variants: [
          {
            weight: '100 1000',
            style: 'normal',
            display: 'swap',
            src: ['./src/assets/fonts/google-sans-flex.woff2'],
          },
        ],
      },
    },
    {
      provider: fontProviders.local(),
      name: 'Google Sans Code',
      cssVariable: '--font-mono',
      fallbacks: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      options: {
        variants: [
          {
            weight: '300 800',
            style: 'normal',
            display: 'swap',
            src: ['./src/assets/fonts/google-sans-code.woff2'],
          },
        ],
      },
    },
  ],

  vite: {
    // Worktrees share dependencies, but each dev server needs its own cache.
    cacheDir: new URL('./.astro/vite', import.meta.url).pathname,
    build: {
      // Keep light-dark(), @layer, relative color syntax and @property untouched.
      // The gBreeze stylesheets rely on them and scoped color-scheme flips need
      // light-dark() to survive to the browser.
      cssTarget: 'esnext',
    },
  },

});
