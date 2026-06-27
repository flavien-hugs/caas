<script lang="ts">
  import { getBlockDef } from '$blocks/registry';

  let { data, form } = $props();
</script>

<svelte:head>
  <title>{data.page.title}</title>
</svelte:head>

<main class="bg-background min-h-screen">
  {#each data.page.blocks as block (block.id)}
    {@const def = getBlockDef(block.type)}
    {#if def}
      {@const Component = def.component}
      <Component props={block.props} mode="preview" {form} />
    {/if}
  {/each}
</main>
