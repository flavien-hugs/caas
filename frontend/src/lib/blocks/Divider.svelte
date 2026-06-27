<script lang="ts">
  import type { DividerProps } from './types';

  let { props }: { props: DividerProps; mode?: 'edit' | 'preview' } = $props();

  const borderStyle = $derived(
    props.variant === 'dashed'
      ? 'border-dashed'
      : props.variant === 'dotted'
        ? 'border-dotted'
        : 'border-solid'
  );
  const borderColor = $derived(
    props.color === 'foreground'
      ? 'border-foreground/30'
      : props.color === 'primary'
        ? 'border-primary/40'
        : 'border-muted-foreground/20'
  );
</script>

<div class="px-6 py-6">
  <hr class="border-t {borderStyle} {borderColor}" />
</div>
