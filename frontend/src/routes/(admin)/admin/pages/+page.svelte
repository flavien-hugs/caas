<script lang="ts">
  import { enhance } from '$app/forms';
  import {
    Plus,
    FileText,
    Eye,
    EyeOff,
    ExternalLink,
    Trash2,
    Hash,
    Type,
    Search,
    X
  } from 'lucide-svelte';
  import { Button, Card, Combobox, ConfirmDialog, Drawer, Input, Label } from '$lib/components/ui';
  import type { ApiPage } from '$lib/api/client';

  let { data, form } = $props();

  const formatDate = (iso: string) =>
    new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(
      new Date(iso)
    );

  // --- Create (drawer) -------------------------------------------------------
  let createOpen = $state(false);
  let creating = $state(false);
  let title = $state('');
  let slug = $state('');
  let slugTouched = $state(false);

  function deriveSlug(t: string): string {
    return t
      .toLowerCase()
      .normalize('NFD')
      .replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 80);
  }

  // Auto-derive the slug from the title until the user edits it by hand.
  $effect(() => {
    if (createOpen && !slugTouched) slug = deriveSlug(title);
  });

  function openCreate() {
    title = '';
    slug = '';
    slugTouched = false;
    createOpen = true;
  }

  // --- Delete (confirm dialog) ----------------------------------------------
  let deleteTarget = $state<ApiPage | null>(null);
  let deleting = $state(false);

  // --- List filtering (client-side: the API returns the full list) ----------
  const STATUS_OPTS = [
    { value: 'all', label: 'Tous les statuts' },
    { value: 'published', label: 'Publiées' },
    { value: 'draft', label: 'Brouillons' }
  ];
  const SORT_OPTS = [
    { value: 'recent', label: 'Plus récentes' },
    { value: 'title', label: 'Titre (A→Z)' }
  ];

  let search = $state('');
  let statusFilter = $state('all');
  let sort = $state('recent');

  const publishedCount = $derived(data.pages.filter((p) => p.status === 'published').length);
  const hasFilters = $derived(search.trim() !== '' || statusFilter !== 'all');

  const filtered = $derived.by(() => {
    const q = search.trim().toLowerCase();
    const list = data.pages.filter((p) => {
      if (statusFilter !== 'all' && p.status !== statusFilter) return false;
      if (q && !`${p.title} ${p.slug}`.toLowerCase().includes(q)) return false;
      return true;
    });
    return list.sort((a, b) =>
      sort === 'title'
        ? a.title.localeCompare(b.title, 'fr')
        : new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    );
  });

  function resetFilters() {
    search = '';
    statusFilter = 'all';
  }
</script>

<svelte:head>
  <title>Pages · CaaS</title>
</svelte:head>

<header class="mb-6 flex items-center justify-between">
  <div>
    <h1 class="text-2xl font-semibold tracking-tight">Pages</h1>
    <p class="text-muted-foreground mt-1 text-sm">
      Construisez et publiez vos landings avec le builder.
    </p>
  </div>
  <Button onclick={openCreate}>
    <Plus class="h-4 w-4" /> Nouvelle page
  </Button>
</header>

{#if data.pages.length === 0}
  <Card class="flex flex-col items-center justify-center p-12 text-center">
    <FileText class="text-muted-foreground h-10 w-10" />
    <p class="mt-4 font-medium">Aucune page pour l'instant</p>
    <p class="text-muted-foreground mt-1 text-sm">Crée ta première page pour commencer.</p>
    <Button class="mt-4" onclick={openCreate}><Plus class="h-4 w-4" /> Nouvelle page</Button>
  </Card>
{:else}
  <!-- Toolbar : recherche + filtre statut + tri -->
  <div class="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center">
    <div class="relative flex-1">
      <Search
        class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
      />
      <Input bind:value={search} placeholder="Rechercher par titre ou slug…" class="pl-9" />
    </div>
    <Combobox
      bind:value={statusFilter}
      options={STATUS_OPTS}
      clearable={false}
      class="sm:w-44"
      placeholder="Statut…"
    />
    <Combobox
      bind:value={sort}
      options={SORT_OPTS}
      clearable={false}
      class="sm:w-44"
      placeholder="Trier…"
    />
  </div>

  <p class="text-muted-foreground mb-3 text-xs">
    {filtered.length}
    {filtered.length > 1 ? 'pages' : 'page'}
    {#if hasFilters}sur {data.pages.length}{:else}· {publishedCount} publiée{publishedCount > 1
        ? 's'
        : ''}{/if}
  </p>

  {#if filtered.length === 0}
    <Card class="flex flex-col items-center justify-center p-12 text-center">
      <Search class="text-muted-foreground h-8 w-8" />
      <p class="mt-3 font-medium">Aucune page ne correspond</p>
      <p class="text-muted-foreground mt-1 text-sm">Aucun résultat pour ces filtres.</p>
      <Button type="button" variant="outline" size="sm" class="mt-4" onclick={resetFilters}>
        <X class="h-3.5 w-3.5" /> Effacer les filtres
      </Button>
    </Card>
  {:else}
    <Card class="overflow-hidden">
      <ul class="divide-y">
        {#each filtered as page (page.id)}
          <li class="hover:bg-muted/30 flex items-center justify-between gap-3 px-4 py-3">
            <a href={`/admin/pages/${page.id}`} class="flex min-w-0 flex-1 items-center gap-3">
              <FileText class="text-muted-foreground h-4 w-4 shrink-0" />
              <div class="min-w-0">
                <p class="truncate font-medium">{page.title}</p>
                <p class="text-muted-foreground truncate text-xs">/{page.slug}</p>
              </div>
            </a>

            <div class="flex shrink-0 items-center gap-3">
              <span
                class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium {page.status ===
                'published'
                  ? 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20'
                  : 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/20'}"
              >
                {#if page.status === 'published'}
                  <Eye class="h-3 w-3" /> Publiée
                {:else}
                  <EyeOff class="h-3 w-3" /> Brouillon
                {/if}
              </span>
              <span class="text-muted-foreground hidden text-xs sm:inline">
                {formatDate(page.updated_at)}
              </span>
              {#if page.status === 'published'}
                <a
                  href={`/p/${page.slug}`}
                  target="_blank"
                  rel="noopener"
                  aria-label="Voir la page publique"
                  class="text-muted-foreground hover:text-foreground"
                >
                  <ExternalLink class="h-4 w-4" />
                </a>
              {/if}
              <button
                type="button"
                onclick={() => (deleteTarget = page)}
                aria-label="Supprimer la page"
                title="Supprimer la page"
                class="text-muted-foreground hover:bg-destructive/10 hover:text-destructive focus-visible:ring-ring flex h-8 w-8 items-center justify-center rounded-md transition-colors focus-visible:ring-2 focus-visible:outline-none"
              >
                <Trash2 class="h-4 w-4" />
              </button>
            </div>
          </li>
        {/each}
      </ul>
    </Card>
  {/if}
{/if}

<!-- Create drawer -->
<Drawer
  bind:open={createOpen}
  title="Nouvelle page"
  description="Choisis un titre et un slug. Tu pourras les modifier plus tard."
>
  <form
    id="create-page-form"
    method="POST"
    action="?/create"
    use:enhance={() => {
      creating = true;
      return async ({ result, update }) => {
        await update();
        creating = false;
        if (result.type !== 'failure') createOpen = false;
      };
    }}
    class="space-y-4"
  >
    <div class="space-y-2">
      <Label for="page-title">Titre</Label>
      <div class="relative">
        <Type
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
        />
        <Input
          id="page-title"
          name="title"
          required
          bind:value={title}
          placeholder="Lutte contre la fraude"
          class="pl-9"
        />
      </div>
    </div>

    <div class="space-y-2">
      <Label for="page-slug">Slug (URL)</Label>
      <div class="relative">
        <Hash
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
        />
        <Input
          id="page-slug"
          name="slug"
          required
          bind:value={slug}
          oninput={() => (slugTouched = true)}
          placeholder="lutte-contre-fraude"
          class="pl-9"
        />
      </div>
      <p class="text-muted-foreground text-xs">
        Lettres minuscules, chiffres et tirets. La page sera publiée sur
        <code class="bg-muted rounded px-1 py-0.5">/p/{slug || 'votre-slug'}</code>.
      </p>
    </div>

    {#if form?.scope === 'create' && form?.error}
      <p
        class="border-destructive/30 bg-destructive/5 text-destructive rounded-md border p-2 text-sm"
      >
        {form.error}
      </p>
    {/if}
  </form>

  {#snippet footer()}
    <div class="flex items-center justify-end gap-2">
      <Button type="button" variant="outline" onclick={() => (createOpen = false)}>Annuler</Button>
      <Button type="submit" form="create-page-form" disabled={creating}>
        {creating ? 'Création…' : 'Créer la page'}
      </Button>
    </div>
  {/snippet}
</Drawer>

<!-- Delete confirmation -->
<ConfirmDialog
  open={deleteTarget !== null}
  title="Supprimer la page"
  description={deleteTarget
    ? `« ${deleteTarget.title} » et son contenu seront définitivement supprimés. Cette action est irréversible.`
    : ''}
  confirmLabel="Supprimer"
  destructive
  loading={deleting}
  confirmForm="delete-page-form"
  onclose={() => (deleteTarget = null)}
>
  <form
    id="delete-page-form"
    method="POST"
    action="?/delete"
    use:enhance={() => {
      deleting = true;
      return async ({ result, update }) => {
        await update();
        deleting = false;
        if (result.type !== 'failure') deleteTarget = null;
      };
    }}
  >
    <input type="hidden" name="id" value={deleteTarget?.id} />
    {#if form?.scope === 'delete' && form?.error}
      <p class="text-destructive mt-3 text-sm">{form.error}</p>
    {/if}
  </form>
</ConfirmDialog>
