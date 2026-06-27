<script lang="ts">
  import { Copy, Trash2, GripVertical } from 'lucide-svelte';
  import { cn } from '$lib/utils';
  import type { Block } from '$blocks/types';
  import type { BuilderStore } from './store.svelte';

  let {
    block,
    store,
    children
  }: {
    block: Block;
    store: BuilderStore;
    children: import('svelte').Snippet;
  } = $props();

  const isSelected = $derived(store.selectedBlockId === block.id);
</script>

<div
  class={cn(
    'group relative cursor-pointer rounded-md ring-1 ring-transparent transition',
    isSelected ? 'ring-primary' : 'hover:ring-input'
  )}
  role="button"
  tabindex="0"
  onclick={(e) => {
    e.stopPropagation();
    store.selectBlock(block.id);
  }}
  onkeydown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      store.selectBlock(block.id);
    }
  }}
>
  <div
    class={cn(
      'absolute top-1/2 -left-3 -translate-y-1/2 opacity-0 transition-opacity',
      isSelected ? 'opacity-100' : 'group-hover:opacity-100'
    )}
  >
    <span
      class="bg-background ring-input flex h-7 w-7 cursor-grab items-center justify-center rounded shadow-sm ring-1"
    >
      <GripVertical class="text-muted-foreground h-4 w-4" />
    </span>
  </div>

  <div
    class={cn(
      'absolute top-2 right-2 z-10 flex gap-1 opacity-0 transition-opacity',
      isSelected ? 'opacity-100' : 'group-hover:opacity-100'
    )}
  >
    <button
      type="button"
      onclick={(e) => {
        e.stopPropagation();
        store.duplicateBlock(block.id);
      }}
      aria-label="Dupliquer"
      class="bg-background text-muted-foreground ring-input hover:text-foreground flex h-7 w-7 items-center justify-center rounded shadow-sm ring-1"
    >
      <Copy class="h-3.5 w-3.5" />
    </button>
    <button
      type="button"
      onclick={(e) => {
        e.stopPropagation();
        store.removeBlock(block.id);
      }}
      aria-label="Supprimer"
      class="bg-background text-destructive ring-input hover:bg-destructive/10 flex h-7 w-7 items-center justify-center rounded shadow-sm ring-1"
    >
      <Trash2 class="h-3.5 w-3.5" />
    </button>
  </div>

  <div class="pointer-events-none">
    {@render children()}
  </div>
</div>
