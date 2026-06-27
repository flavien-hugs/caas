<script lang="ts">
  import { getBlockDef } from './registry';
  import type { Block, SectionProps } from './types';

  interface Props {
    props: SectionProps;
    mode?: 'edit' | 'preview';
    /** When supplied, lets the editor wrap each child with selection chrome
     *  via `BlockWrapper`. Public render leaves it undefined → plain output. */
    childRenderer?: (block: Block, columnIndex: number, blockIndex: number) => unknown;
  }

  let { props, mode = 'preview' }: Props = $props();

  const cols = $derived(Math.min(4, Math.max(1, props.columns ?? 2)));

  const gridColsClass = $derived(
    {
      1: 'grid-cols-1',
      2: 'grid-cols-1 md:grid-cols-2',
      3: 'grid-cols-1 md:grid-cols-3',
      4: 'grid-cols-2 lg:grid-cols-4'
    }[cols]
  );

  const gridTemplateClass = $derived(
    props.layout === 'sidebar-left' && cols === 2
      ? 'md:grid-cols-[minmax(0,1fr)_2fr]'
      : props.layout === 'sidebar-right' && cols === 2
        ? 'md:grid-cols-[2fr_minmax(0,1fr)]'
        : ''
  );

  const gapClass = $derived(
    { none: 'gap-0', sm: 'gap-3', md: 'gap-6', lg: 'gap-10' }[props.gap ?? 'md']
  );

  const alignClass = $derived(
    {
      start: 'items-start',
      center: 'items-center',
      end: 'items-end',
      stretch: 'items-stretch'
    }[props.align ?? 'start']
  );

  // Normalise children: always render exactly `cols` columns; trim or pad
  // with empty arrays so the user sees the right shape even if the JSON
  // payload is out of sync (e.g. after changing `columns`).
  const normalisedChildren: Block[][] = $derived(
    Array.from({ length: cols }, (_, i) => (props.children?.[i] ?? []) as Block[])
  );
</script>

<section class="grid {gridColsClass} {gridTemplateClass} {gapClass} {alignClass}">
  {#each normalisedChildren as column, ci (ci)}
    <div class="flex min-w-0 flex-col gap-4">
      {#if column.length === 0 && mode === 'edit'}
        <div
          class="border-muted-foreground/20 text-muted-foreground flex min-h-[100px] items-center justify-center rounded-md border-2 border-dashed text-xs"
        >
          Colonne {ci + 1} vide — glisse un bloc ici.
        </div>
      {/if}
      {#each column as child (child.id)}
        {@const def = getBlockDef(child.type)}
        {#if def}
          {@const Component = def.component}
          <Component props={child.props} {mode} />
        {:else}
          <div
            class="border-destructive/30 bg-destructive/5 text-destructive rounded-md border p-3 text-xs"
          >
            Bloc inconnu : <code>{child.type}</code>
          </div>
        {/if}
      {/each}
    </div>
  {/each}
</section>
