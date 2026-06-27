<script lang="ts">
  import type { ImageProps } from './types';

  let { props, mode = 'preview' }: { props: ImageProps; mode?: 'edit' | 'preview' } = $props();

  const fitClass = $derived(props.fit === 'contain' ? 'object-contain' : 'object-cover');
  const radiusClass = $derived(
    {
      none: 'rounded-none',
      md: 'rounded-md',
      lg: 'rounded-lg',
      full: 'rounded-full'
    }[props.rounded ?? 'md']
  );
  const maxWidthClass = $derived(
    {
      sm: 'max-w-sm',
      md: 'max-w-md',
      lg: 'max-w-lg',
      xl: 'max-w-2xl',
      full: 'w-full'
    }[props.maxWidth ?? 'lg']
  );
</script>

<figure class="flex justify-center px-6 py-8">
  {#if props.src}
    <img
      src={props.src}
      alt={props.alt ?? ''}
      class="h-auto {maxWidthClass} {fitClass} {radiusClass}"
      loading="lazy"
    />
  {:else if mode === 'edit'}
    <div
      class="border-muted-foreground/20 text-muted-foreground flex h-40 w-full items-center justify-center rounded-md border-2 border-dashed text-sm"
    >
      Renseigne une URL d'image dans le panneau de droite.
    </div>
  {/if}
</figure>
