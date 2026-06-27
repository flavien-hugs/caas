<script lang="ts">
  import type { SpacerProps } from './types';

  let { props, mode = 'preview' }: { props: SpacerProps; mode?: 'edit' | 'preview' } = $props();

  const heightClass = $derived(
    {
      xs: 'h-3',
      sm: 'h-6',
      md: 'h-12',
      lg: 'h-20',
      xl: 'h-32'
    }[props.size ?? 'md']
  );
</script>

<div
  class="{heightClass} {mode === 'edit'
    ? 'border-muted-foreground/20 bg-muted/10 border-2 border-dashed'
    : ''}"
  aria-hidden="true"
></div>
