<script lang="ts">
  import { untrack } from 'svelte';
  import { enhance } from '$app/forms';
  import { ArrowLeft, Save, Eye, EyeOff, ExternalLink, Trash2 } from 'lucide-svelte';
  import { Button, Input } from '$lib/components/ui';
  import { createBuilderStore } from '$lib/builder/store.svelte';
  import BlockLibrary from '$lib/builder/BlockLibrary.svelte';
  import Canvas from '$lib/builder/Canvas.svelte';
  import Inspector from '$lib/builder/Inspector.svelte';
  import type { BlockType } from '$blocks/types';

  let { data, form } = $props();

  // Initial snapshot is read once via untrack; subsequent server refreshes
  // come back via the form-action `$effect` below and call syncFromServer.
  const store = untrack(() =>
    createBuilderStore({
      id: data.page.id,
      slug: data.page.slug,
      title: data.page.title,
      status: data.page.status,
      publishedAt: data.page.published_at,
      blocks: data.page.blocks.map((b) => ({
        id: b.id,
        type: b.type as BlockType,
        props: b.props
      }))
    })
  );

  // When the server replays the page after a successful save/publish/unpublish,
  // re-sync the store so dirty resets and status badges update.
  $effect(() => {
    const next = form && 'page' in form ? form.page : null;
    if (next) {
      store.syncFromServer({
        id: next.id,
        slug: next.slug,
        title: next.title,
        status: next.status,
        publishedAt: next.published_at,
        blocks: next.blocks.map((b) => ({
          id: b.id,
          type: b.type as BlockType,
          props: b.props
        }))
      });
    }
  });

  let saving = $state(false);
  let publishing = $state(false);

  function serializeBlocks(): string {
    return JSON.stringify(store.blocks.map((b) => ({ id: b.id, type: b.type, props: b.props })));
  }
</script>

<svelte:head>
  <title>{store.title} · Éditeur</title>
</svelte:head>

<!-- Editor breaks out of the 6xl admin container to use the full viewport. -->
<div class="-mx-6 -my-5 flex h-[calc(100vh-0px)] flex-col">
  <header class="bg-background flex h-12 shrink-0 items-center justify-between gap-3 border-b px-3">
    <div class="flex min-w-0 flex-1 items-center gap-3">
      <a
        href="/admin/pages"
        class="text-muted-foreground hover:text-foreground shrink-0"
        aria-label="Retour aux pages"
      >
        <ArrowLeft class="h-4 w-4" />
      </a>
      <Input
        value={store.title}
        oninput={(e) => store.setTitle(e.currentTarget.value)}
        class="hover:border-input focus-visible:border-input h-8 w-64 shrink-0 border-transparent text-sm font-medium"
      />
      <span class="text-muted-foreground hidden shrink-0 text-xs whitespace-nowrap sm:inline">
        /{store.slug}
      </span>
      {#if store.dirty}
        <span
          class="hidden shrink-0 items-center gap-1 text-xs whitespace-nowrap text-amber-600 md:inline-flex"
        >
          • Modifications non enregistrées
        </span>
      {/if}
      {#if form?.error}
        <span class="text-destructive truncate text-xs">{form.error}</span>
      {/if}
    </div>

    <div class="flex items-center gap-2">
      {#if store.status === 'published'}
        <a
          href={`/p/${store.slug}`}
          target="_blank"
          rel="noopener"
          class="text-muted-foreground hover:text-foreground inline-flex items-center gap-1 text-xs"
        >
          <ExternalLink class="h-3.5 w-3.5" /> Voir
        </a>
      {/if}

      <form
        method="POST"
        action="?/save"
        use:enhance={() => {
          saving = true;
          return async ({ update }) => {
            await update();
            saving = false;
          };
        }}
        class="contents"
      >
        <input type="hidden" name="title" value={store.title} />
        <input type="hidden" name="slug" value={store.slug} />
        <input type="hidden" name="blocks" value={serializeBlocks()} />
        <Button type="submit" variant="outline" size="sm" disabled={saving || !store.dirty}>
          <Save class="h-3.5 w-3.5" />
          {saving ? 'Enregistrement…' : 'Enregistrer'}
        </Button>
      </form>

      {#if store.status === 'published'}
        <form
          method="POST"
          action="?/unpublish"
          use:enhance={() => {
            publishing = true;
            return async ({ update }) => {
              await update();
              publishing = false;
            };
          }}
          class="contents"
        >
          <Button type="submit" variant="outline" size="sm" disabled={publishing}>
            <EyeOff class="h-3.5 w-3.5" />
            {publishing ? '…' : 'Dépublier'}
          </Button>
        </form>
      {:else}
        <form
          method="POST"
          action="?/publish"
          use:enhance={() => {
            publishing = true;
            return async ({ update }) => {
              await update();
              publishing = false;
            };
          }}
          class="contents"
        >
          <Button type="submit" size="sm" disabled={publishing || store.dirty}>
            <Eye class="h-3.5 w-3.5" />
            {publishing ? '…' : 'Publier'}
          </Button>
        </form>
      {/if}

      <form
        method="POST"
        action="?/delete"
        use:enhance={({ cancel }) => {
          if (!confirm('Supprimer définitivement cette page ?')) cancel();
          return async ({ update }) => {
            await update();
          };
        }}
        class="contents"
      >
        <Button type="submit" variant="outline" size="icon" aria-label="Supprimer">
          <Trash2 class="text-destructive h-3.5 w-3.5" />
        </Button>
      </form>
    </div>
  </header>

  <div class="flex flex-1 overflow-hidden">
    <BlockLibrary {store} />
    <Canvas {store} />
    <Inspector {store} />
  </div>
</div>
