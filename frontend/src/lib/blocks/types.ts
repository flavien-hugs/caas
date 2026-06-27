/**
 * Block schemas — single source of truth for the page builder.
 *
 * The backend stores ``Block.props`` as opaque JSON, so this file is the
 * only place where the per-type contract lives. Adding a new block type
 * means:
 *   1. add a Zod schema below;
 *   2. add an entry to ``BLOCK_DEFS`` in ``registry.ts``;
 *   3. add a Svelte component in ``lib/blocks/<Name>.svelte`` accepting
 *      ``{ props, mode: 'edit' | 'preview' }``.
 *
 * No backend deploy needed.
 *
 * D1 evolution: every block can carry an optional ``StyleProps`` blob
 * shared via ``style.ts``. ``section`` blocks are containers — their
 * ``props.children`` is a recursive ``Block[][]`` (one array per column).
 */

import { z } from 'zod';

// ---- per-block prop schemas -------------------------------------------------

export const HeroProps = z.object({
  headline: z.string().min(1, 'Le titre est requis.').max(200),
  subheadline: z.string().max(400).optional().default(''),
  ctaLabel: z.string().max(60).optional().default(''),
  ctaHref: z.string().url('URL invalide.').optional().or(z.literal('')),
  background: z.enum(['light', 'dark', 'gradient']).default('light')
});
export type HeroProps = z.infer<typeof HeroProps>;

const FeatureItem = z.object({
  title: z.string().min(1).max(80),
  body: z.string().max(280).default('')
});

export const FeatureGridProps = z.object({
  headline: z.string().max(200).optional().default(''),
  items: z
    .array(FeatureItem)
    .min(1, 'Ajoute au moins une fonctionnalité.')
    .max(8)
    .default([{ title: 'Fonctionnalité', body: '' }])
});
export type FeatureGridProps = z.infer<typeof FeatureGridProps>;

const FaqItem = z.object({
  question: z.string().min(1).max(200),
  answer: z.string().min(1).max(2000)
});

export const FAQProps = z.object({
  headline: z.string().max(200).optional().default('Questions fréquentes'),
  items: z
    .array(FaqItem)
    .min(1)
    .max(20)
    .default([{ question: 'Question…', answer: 'Réponse…' }])
});
export type FAQProps = z.infer<typeof FAQProps>;

export const CTAButtonProps = z.object({
  label: z.string().min(1, 'Libellé requis.').max(60),
  href: z.string().url('URL invalide.'),
  variant: z.enum(['default', 'secondary', 'outline']).default('default'),
  align: z.enum(['left', 'center', 'right']).default('center')
});
export type CTAButtonProps = z.infer<typeof CTAButtonProps>;

export const RichTextProps = z.object({
  // Plain Markdown for now — kept stringly-typed to avoid leaking a parser
  // contract into the schema. The component decides how to render.
  markdown: z.string().min(1, 'Le contenu est vide.').max(20000)
});
export type RichTextProps = z.infer<typeof RichTextProps>;

export const PaymentFormProps = z.object({
  // Identifier of the product/book in the backend catalog (e.g.
  // "lutte-contre-fraude"). The PaymentForm block delegates to the
  // existing /purchases flow on submit.
  bookId: z.string().min(1, 'book_id requis.').max(80),
  title: z.string().max(80).optional().default(''),
  ctaLabel: z.string().max(60).default('Payer maintenant'),
  amountHint: z.string().max(100).optional().default(''),
  // Appearance — how the form renders. Optional with defaults so existing
  // pages keep validating.
  align: z.enum(['left', 'center']).default('center'),
  width: z.enum(['sm', 'md', 'lg']).default('md'),
  variant: z.enum(['card', 'plain']).default('card'),
  cardBackground: z.enum(['card', 'muted', 'accent']).default('card'),
  ctaVariant: z.enum(['default', 'secondary', 'outline']).default('default')
});
export type PaymentFormProps = z.infer<typeof PaymentFormProps>;

// ---- D1 primitive blocks ----------------------------------------------------

export const SpacerProps = z.object({
  // Vertical breathing room. Tied to the preset enum so the spacer composes
  // with ``style.paddingY`` rather than fighting it on every block.
  size: z.enum(['xs', 'sm', 'md', 'lg', 'xl']).default('md')
});
export type SpacerProps = z.infer<typeof SpacerProps>;

export const DividerProps = z.object({
  variant: z.enum(['solid', 'dashed', 'dotted']).default('solid'),
  color: z.enum(['muted', 'foreground', 'primary']).default('muted')
});
export type DividerProps = z.infer<typeof DividerProps>;

export const ImageProps = z.object({
  src: z.string().url('URL d’image invalide.'),
  alt: z.string().max(200).default(''),
  fit: z.enum(['contain', 'cover']).default('cover'),
  rounded: z.enum(['none', 'md', 'lg', 'full']).default('md'),
  maxWidth: z.enum(['sm', 'md', 'lg', 'xl', 'full']).default('lg')
});
export type ImageProps = z.infer<typeof ImageProps>;

// ---- Section (D1 container) -------------------------------------------------

// ``z.lazy`` lets the Section schema reference Block recursively.
// We don't validate the children's per-type props here — each child block's
// schema runs separately when it's mutated by the inspector. Section only
// validates structure: an array (per column) of arrays of {id, type, props}.
const AnyBlock = z.object({
  id: z.string().min(1),
  type: z.string().min(1),
  props: z.record(z.unknown()).default({})
});

export const SectionProps = z.object({
  columns: z.number().int().min(1).max(4).default(2),
  gap: z.enum(['none', 'sm', 'md', 'lg']).default('md'),
  layout: z.enum(['equal', 'sidebar-left', 'sidebar-right']).default('equal'),
  align: z.enum(['start', 'center', 'end', 'stretch']).default('start'),
  // children[i] = blocks in column i. Length should match ``columns``,
  // missing/extra columns are normalised at render time.
  children: z.array(z.array(AnyBlock)).default([[], []])
});
export type SectionProps = z.infer<typeof SectionProps>;

// ---- discriminated union ----------------------------------------------------

export const BlockType = z.enum([
  'hero',
  'feature_grid',
  'faq',
  'cta_button',
  'rich_text',
  'payment_form',
  'section',
  'spacer',
  'divider',
  'image'
]);
export type BlockType = z.infer<typeof BlockType>;

export const BLOCK_SCHEMAS = {
  hero: HeroProps,
  feature_grid: FeatureGridProps,
  faq: FAQProps,
  cta_button: CTAButtonProps,
  rich_text: RichTextProps,
  payment_form: PaymentFormProps,
  section: SectionProps,
  spacer: SpacerProps,
  divider: DividerProps,
  image: ImageProps
} as const satisfies Record<BlockType, z.ZodTypeAny>;

export type BlockPropsByType = {
  hero: HeroProps;
  feature_grid: FeatureGridProps;
  faq: FAQProps;
  cta_button: CTAButtonProps;
  rich_text: RichTextProps;
  payment_form: PaymentFormProps;
  section: SectionProps;
  spacer: SpacerProps;
  divider: DividerProps;
  image: ImageProps;
};

export interface Block {
  id: string;
  type: BlockType;
  props: Record<string, unknown>;
}

/** Validate a block's props against its declared type. Returns the parsed,
 *  defaulted props on success; throws ZodError on failure. */
export function validateBlock<T extends BlockType>(type: T, props: unknown): BlockPropsByType[T] {
  return BLOCK_SCHEMAS[type].parse(props) as BlockPropsByType[T];
}

/** Safe variant that returns ``{ success, data | error }`` without throwing. */
export function safeValidateBlock(type: BlockType, props: unknown) {
  return BLOCK_SCHEMAS[type].safeParse(props);
}
