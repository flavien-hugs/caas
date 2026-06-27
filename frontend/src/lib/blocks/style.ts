/**
 * Shared style preset schema used by every block.
 *
 * Enums instead of free-form CSS: the editor exposes a fixed knob set and
 * the renderer maps each token to one or a few Tailwind classes. The
 * tradeoff is intentional — output stays deterministic, theme-coherent, and
 * the inspector stays simple. If someone really needs raw CSS later, a
 * `custom` escape hatch can be added on top.
 */

import { z } from 'zod';

export const StyleProps = z.object({
  background: z
    .enum(['none', 'muted', 'card', 'primary', 'dark', 'gradient'])
    .optional()
    .default('none'),
  textColor: z.enum(['inherit', 'muted', 'primary', 'white']).optional().default('inherit'),
  paddingY: z.enum(['none', 'sm', 'md', 'lg', 'xl']).optional().default('lg'),
  paddingX: z.enum(['none', 'sm', 'md', 'lg']).optional().default('md'),
  align: z.enum(['left', 'center', 'right']).optional().default('left'),
  maxWidth: z.enum(['none', 'narrow', 'normal', 'wide', 'full']).optional().default('normal')
});
export type StyleProps = z.infer<typeof StyleProps>;

const BG: Record<NonNullable<StyleProps['background']>, string> = {
  none: '',
  muted: 'bg-muted/30',
  card: 'bg-card',
  primary: 'bg-primary text-primary-foreground',
  dark: 'bg-slate-900 text-white',
  gradient: 'bg-gradient-to-br from-amber-400 via-orange-500 to-orange-600 text-white'
};

const TEXT: Record<NonNullable<StyleProps['textColor']>, string> = {
  inherit: '',
  muted: 'text-muted-foreground',
  primary: 'text-primary',
  white: 'text-white'
};

const PY: Record<NonNullable<StyleProps['paddingY']>, string> = {
  none: 'py-0',
  sm: 'py-6',
  md: 'py-10',
  lg: 'py-16',
  xl: 'py-24 sm:py-32'
};

const PX: Record<NonNullable<StyleProps['paddingX']>, string> = {
  none: 'px-0',
  sm: 'px-3',
  md: 'px-6',
  lg: 'px-10'
};

// Alignment targets headings only (h1–h3), not the whole block: centering a
// block should center its title, while body copy, lists and CTAs keep their
// natural (left) flow. Scoped via Tailwind arbitrary variants so this stays a
// single source of truth across every block that uses ``innerClasses``.
const ALIGN: Record<NonNullable<StyleProps['align']>, string> = {
  left: '[&_h1]:text-left [&_h2]:text-left [&_h3]:text-left',
  center: '[&_h1]:text-center [&_h2]:text-center [&_h3]:text-center',
  right: '[&_h1]:text-right [&_h2]:text-right [&_h3]:text-right'
};

const MAX_W: Record<NonNullable<StyleProps['maxWidth']>, string> = {
  none: '',
  narrow: 'mx-auto max-w-2xl',
  normal: 'mx-auto max-w-4xl',
  wide: 'mx-auto max-w-6xl',
  full: 'w-full'
};

/** Class string for the outer ``<section>`` element of a block. */
export function outerClasses(s: Partial<StyleProps> | undefined): string {
  const v: Partial<StyleProps> = s ?? {};
  return [
    BG[v.background ?? 'none'],
    TEXT[v.textColor ?? 'inherit'],
    PY[v.paddingY ?? 'lg'],
    PX[v.paddingX ?? 'md']
  ]
    .filter(Boolean)
    .join(' ');
}

/** Class string for the inner ``<div>`` that constrains the content. */
export function innerClasses(s: Partial<StyleProps> | undefined): string {
  const v: Partial<StyleProps> = s ?? {};
  return [MAX_W[v.maxWidth ?? 'normal'], ALIGN[v.align ?? 'left']].filter(Boolean).join(' ');
}

/** Default ``StyleProps`` for legacy blocks that don't carry one yet. Keeps
 *  visual parity with the pre-D1 hard-coded styling. */
export const DEFAULT_STYLE: StyleProps = StyleProps.parse({});
