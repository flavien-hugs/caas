<script lang="ts">
  import type { CTAButtonProps } from './types';
  import { cn } from '$lib/utils';

  let { props }: { props: CTAButtonProps; mode?: 'edit' | 'preview' } = $props();

  const align = $derived(
    props.align === 'left'
      ? 'justify-start'
      : props.align === 'right'
        ? 'justify-end'
        : 'justify-center'
  );
  const variant = $derived(
    props.variant === 'secondary'
      ? 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
      : props.variant === 'outline'
        ? 'border border-input bg-background hover:bg-secondary'
        : 'bg-primary text-primary-foreground hover:bg-primary/90'
  );
</script>

<div class={cn('flex px-6 py-8', align)}>
  <a
    href={props.href}
    class={cn(
      'inline-flex h-11 items-center justify-center rounded-md px-8 text-sm font-medium shadow-sm transition-colors',
      variant
    )}
  >
    {props.label}
  </a>
</div>
