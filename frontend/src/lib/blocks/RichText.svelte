<script lang="ts">
  import { renderMarkdown } from '$lib/markdown';
  import { outerClasses, innerClasses, StyleProps } from './style';
  import type { RichTextProps } from './types';

  let { props }: { props: RichTextProps; mode?: 'edit' | 'preview' } = $props();

  const style = $derived(StyleProps.parse((props as Record<string, unknown>)._style ?? {}));
  const outer = $derived(outerClasses(style));
  const inner = $derived(`${innerClasses(style)} prose prose-slate max-w-none`);

  // Full Markdown (gfm) rendered + sanitized in ``$lib/markdown``.
  const html = $derived(renderMarkdown(props.markdown));
</script>

<section class={outer}>
  <div class={inner}>
    {@html html}
  </div>
</section>
