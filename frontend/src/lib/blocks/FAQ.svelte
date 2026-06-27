<script lang="ts">
  import { renderMarkdown } from '$lib/markdown';
  import { outerClasses, innerClasses, StyleProps } from './style';
  import type { FAQProps } from './types';

  let { props }: { props: FAQProps; mode?: 'edit' | 'preview' } = $props();

  const style = $derived(StyleProps.parse((props as Record<string, unknown>)._style ?? {}));
  const legacyMuted = $derived(style.background === 'none' ? 'bg-muted/30' : '');
  const outer = $derived(`${outerClasses(style)} ${legacyMuted}`.trim());
  const inner = $derived(innerClasses(style));
</script>

<section class={outer}>
  <div class={inner}>
    {#if props.headline}
      <h2 class="text-2xl font-semibold tracking-tight sm:text-3xl">{props.headline}</h2>
    {/if}

    <div class="mt-8 space-y-3">
      {#each props.items as item, i (i)}
        <details class="group bg-background rounded-lg border p-5">
          <summary class="flex cursor-pointer items-center justify-between text-base font-medium">
            <span>{item.question}</span>
            <span class="text-muted-foreground ml-4 transition group-open:rotate-180">⌄</span>
          </summary>
          <div class="prose prose-sm prose-slate text-muted-foreground mt-3 max-w-none">
            {@html renderMarkdown(item.answer)}
          </div>
        </details>
      {/each}
    </div>
  </div>
</section>
