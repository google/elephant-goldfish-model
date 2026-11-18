import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

export const collections = {
  docs: defineCollection({
    loader: glob({
      base: '..',
      pattern: 'docs/site/**/*.md',
      generateId: ({ entry }) => entry.replace('docs/site/', '').replace(/\.md$/, ''),
    }),
    schema: docsSchema(),
  }),
};
