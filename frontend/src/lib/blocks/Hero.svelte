<script lang="ts">
  import { renderMarkdownInline } from '$lib/markdown';
  import { outerClasses, innerClasses, StyleProps } from './style';
  import type { HeroProps } from './types';

  let { props, mode = 'preview' }: { props: HeroProps; mode?: 'edit' | 'preview' } = $props();

  // `_style` is an optional sibling of the block's own props. When present
  // it overrides the legacy `background` enum and lets the user dial in
  // padding / alignment / colors.
  const style = $derived(StyleProps.parse((props as Record<string, unknown>)._style ?? {}));

  // Legacy fallback: when no `_style.background` is set, honour the original
  // ``background`` prop so seeded pages render identically.
  const legacyBg = $derived(
    style.background === 'none'
      ? props.background === 'dark'
        ? 'bg-slate-900 text-white'
        : props.background === 'gradient'
          ? 'bg-gradient-to-br from-amber-400 via-orange-500 to-orange-600 text-white'
          : 'bg-white text-slate-900'
      : ''
  );

  const outer = $derived(`${outerClasses(style)} ${legacyBg}`.trim());
  const inner = $derived(innerClasses(style));
</script>

<section class={outer}>
  <div class={inner}>
    {#if props.headline}
      <h1 class="text-3xl font-bold tracking-tight sm:text-5xl">{props.headline}</h1>
    {:else if mode === 'edit'}
      <h1 class="text-3xl font-bold tracking-tight opacity-40 sm:text-5xl">Titre du hero…</h1>
    {/if}

    {#if props.subheadline}
      <p class="mt-4 text-base opacity-90 sm:text-lg">
        {@html renderMarkdownInline(props.subheadline)}
      </p>
    {/if}

    {#if props.ctaLabel && props.ctaHref}
      <a
        href={props.ctaHref}
        class="mt-8 inline-flex items-center justify-center rounded-md bg-white px-6 py-3 text-sm font-medium text-slate-900 shadow-sm hover:bg-slate-100"
      >
        {props.ctaLabel}
      </a>
    {/if}
  </div>
</section>
