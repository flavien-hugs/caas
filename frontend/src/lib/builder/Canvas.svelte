<script lang="ts">
  import { dndzone, type DndEvent } from 'svelte-dnd-action';
  import { flip } from 'svelte/animate';
  import { Plus } from 'lucide-svelte';
  import { getBlockDef } from '$blocks/registry';
  import type { Block } from '$blocks/types';
  import BlockWrapper from './BlockWrapper.svelte';
  import type { BuilderStore } from './store.svelte';

  let { store }: { store: BuilderStore } = $props();

  // svelte-dnd-action mutates the array; we hand it a freshly-derived list
  // and write back via setBlocks on finalize.
  function handleConsider(e: CustomEvent<DndEvent<Block>>) {
    store.setBlocks(e.detail.items);
  }
  function handleFinalize(e: CustomEvent<DndEvent<Block>>) {
    store.setBlocks(e.detail.items);
  }
</script>

<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
<main
  class="bg-background flex-1 overflow-y-auto"
  role="region"
  aria-label="Canvas"
  onclick={() => store.selectBlock(null)}
  onkeydown={(e) => e.key === 'Escape' && store.selectBlock(null)}
>
  <div class="p-1">
    {#if store.blocks.length === 0}
      <div
        class="flex flex-col items-center justify-center rounded-lg border-2 border-dashed py-24 text-center"
      >
        <Plus class="text-muted-foreground h-8 w-8" />
        <p class="mt-3 text-sm font-medium">Page vide</p>
        <p class="text-muted-foreground mt-1 text-xs">
          Choisis un bloc dans le panneau de gauche pour commencer.
        </p>
      </div>
    {:else}
      <div
        class="space-y-3"
        use:dndzone={{
          items: store.blocks,
          flipDurationMs: 150,
          dropTargetStyle: { outline: '2px dashed rgb(99 102 241 / 0.5)' }
        }}
        onconsider={handleConsider}
        onfinalize={handleFinalize}
      >
        {#each store.blocks as block (block.id)}
          {@const def = getBlockDef(block.type)}
          <div animate:flip={{ duration: 150 }}>
            {#if def}
              {@const Component = def.component}
              <BlockWrapper {block} {store}>
                <Component props={block.props} mode="edit" />
              </BlockWrapper>
            {:else}
              <div
                class="border-destructive/40 bg-destructive/5 text-destructive rounded-md border p-4 text-sm"
              >
                Type de bloc inconnu : <code>{block.type}</code>
              </div>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
</main>
