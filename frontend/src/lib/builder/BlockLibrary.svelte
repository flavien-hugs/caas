<script lang="ts">
  import { BLOCK_DEFS, BLOCK_TYPES_ORDERED, type BlockDef } from '$blocks/registry';
  import type { BlockType } from '$blocks/types';
  import type { BuilderStore } from './store.svelte';

  let { store }: { store: BuilderStore } = $props();

  const CATEGORY_LABEL: Record<BlockDef['category'], string> = {
    layout: 'Mise en page',
    content: 'Contenu',
    media: 'Média',
    interaction: 'Interaction'
  };

  // Group BLOCK_TYPES_ORDERED by category while preserving order.
  const grouped = $derived(
    BLOCK_TYPES_ORDERED.reduce<Record<BlockDef['category'], BlockType[]>>(
      (acc, type) => {
        const cat = BLOCK_DEFS[type].category;
        (acc[cat] ??= []).push(type);
        return acc;
      },
      {} as Record<BlockDef['category'], BlockType[]>
    )
  );

  const CATEGORY_ORDER: BlockDef['category'][] = ['layout', 'content', 'media', 'interaction'];
</script>

<aside class="bg-muted/30 w-full shrink-0 border-r p-2 md:w-56">
  <div class="space-y-4">
    {#each CATEGORY_ORDER as category (category)}
      {#if grouped[category]?.length}
        <div>
          <h2 class="text-muted-foreground px-1 text-[10px] font-semibold tracking-wide uppercase">
            {CATEGORY_LABEL[category]}
          </h2>
          <ul class="mt-1.5 space-y-1">
            {#each grouped[category] as type (type)}
              {@const def = BLOCK_DEFS[type]}
              {@const Icon = def.icon}
              <li>
                <button
                  type="button"
                  onclick={() => store.addBlock(type)}
                  title={def.description}
                  class="group bg-background hover:border-input flex w-full items-start gap-2 rounded-md border border-transparent p-2 text-left text-sm transition-colors hover:shadow-sm"
                >
                  <Icon
                    class="text-muted-foreground group-hover:text-foreground mt-0.5 h-4 w-4 shrink-0"
                  />
                  <span class="min-w-0">
                    <span class="block text-xs leading-tight font-medium">{def.label}</span>
                    <span class="text-muted-foreground block truncate text-[10px]">
                      {def.description}
                    </span>
                  </span>
                </button>
              </li>
            {/each}
          </ul>
        </div>
      {/if}
    {/each}
  </div>
</aside>
