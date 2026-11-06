import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';
import { docsSchema } from '@astrojs/starlight/schema';

const titles: Record<string, string> = {
  'egm-brainstorm': 'Brainstorm', 'egm-draft': 'Draft', 'egm-review': 'Review',
  'egm-resolve': 'Resolve findings', 'egm-review-loop': 'Custom review',
  'egm-bootstrap': 'Document a codebase', 'egm-drift-report': 'Check for drift',
};

export const collections = {
  docs: defineCollection({
    loader: glob({
      base: '..',
      pattern: ['docs/site/*.md', 'skills/*/SKILL.md'],
      generateId: ({ entry, data }) => entry.startsWith('skills/')
        ? `skills/${data.name}` : entry.replace('docs/site/', '').replace(/\.md$/, ''),
    }),
    schema: context => z.preprocess(value => {
      const data = value as Record<string, unknown>;
      return { ...data, title: data.title ?? titles[String(data.name)] };
    }, docsSchema()(context)),
  }),
};
