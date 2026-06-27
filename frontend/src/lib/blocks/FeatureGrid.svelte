<script lang="ts">
  import { renderMarkdown } from '$lib/markdown';
  import { outerClasses, innerClasses, StyleProps } from './style';
  import type { FeatureGridProps } from './types';

  let { props, mode = 'preview' }: { props: FeatureGridProps; mode?: 'edit' | 'preview' } =
    $props();

  const style = $derived(StyleProps.parse((props as Record<string, unknown>)._style ?? {}));
  const outer = $derived(outerClasses(style));
  const inner = $derived(innerClasses(style) || 'mx-auto max-w-5xl');
</script>

<section class={outer}>
  <div class={inner}>
    {#if props.headline}
      <h2 class="text-2xl font-semibold tracking-tight sm:text-3xl">{props.headline}</h2>
    {/if}

    <div class="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {#each props.items as item, i (i)}
        <div class="bg-card rounded-lg border p-5">
          <h3 class="font-medium">{item.title || (mode === 'edit' ? 'Titre…' : '')}</h3>
          {#if item.body}
            <div class="prose prose-sm prose-slate text-muted-foreground mt-2 max-w-none">
              {@html renderMarkdown(item.body)}
            </div>
          {/if}
        </div>
      {/each}
    </div>
  </div>
</section>
