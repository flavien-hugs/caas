<script lang="ts">
  import { untrack, tick } from 'svelte';
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import { navigating } from '$app/state';
  import {
    Search,
    Download,
    RefreshCw,
    MailCheck,
    ChevronLeft,
    ChevronRight,
    CheckCircle2,
    XCircle,
    Clock,
    AlertCircle,
    X
  } from 'lucide-svelte';
  import {
    Button,
    buttonVariants,
    Card,
    Combobox,
    Drawer,
    Input,
    Label,
    type ComboboxOption
  } from '$lib/components/ui';
  import { cn } from '$lib/utils';
  import type { ApiTransaction, TransactionFilters } from '$lib/api/client';

  const STATUS_OPTIONS: ComboboxOption[] = [
    { value: 'SUCCESS', label: 'Payée', description: 'Paiement confirmé par le provider' },
    { value: 'PENDING', label: 'En attente', description: 'Initiée, pas encore confirmée' },
    { value: 'FAILED', label: 'Échouée', description: 'Refus côté provider' },
    { value: 'SECURITY_ERROR', label: 'Anomalie', description: 'Vérification de sécurité échouée' }
  ];

  // The xlsx download is a same-origin SvelteKit proxy
  // (``/admin/transactions/export.xlsx/+server.ts``). We build the query
  // inline rather than importing the server-only ``$lib/api/client``,
  // which would pull ``$lib/server/env`` (BACKEND_BASE) into the
  // browser bundle.
  function buildExportUrl(filters: TransactionFilters): string {
    const sp = new URLSearchParams();
    if (filters.search) sp.set('search', filters.search);
    if (filters.status) sp.set('status', filters.status);
    if (filters.book_id) sp.set('book_id', filters.book_id);
    if (filters.start_date) sp.set('start_date', filters.start_date);
    if (filters.end_date) sp.set('end_date', filters.end_date);
    if (filters.include_low_amount) sp.set('include_low_amount', 'true');
    const s = sp.toString();
    return `/admin/transactions/export.xlsx${s ? '?' + s : ''}`;
  }

  let { data, form } = $props();

  // Filter inputs are seeded from server-side `data.filters`; on submit the
  // form navigates with `goto(?…)` so back/forward stays consistent.
  let search = $state(untrack(() => data.filters.search ?? ''));
  let status = $state(untrack(() => data.filters.status ?? ''));
  let bookId = $state(untrack(() => data.filters.book_id ?? ''));
  let startDate = $state(untrack(() => data.filters.start_date ?? ''));
  let endDate = $state(untrack(() => data.filters.end_date ?? ''));
  let includeLow = $state(untrack(() => Boolean(data.filters.include_low_amount)));

  // Sync drawer — opens for one row at a time (shared Drawer component).
  let syncingId = $state<string | null>(null);
  let syncing = $state(false);
  const syncTarget = $derived(
    syncingId ? (data.result.items.find((t) => t.id === syncingId) ?? null) : null
  );

  // Pending filter request id — set by `pushFilters`, cleared by a paired
  // setTimeout. The latest call wins so rapid keystrokes don't pile up
  // back-to-back navigations.
  let pending: ReturnType<typeof setTimeout> | null = null;

  /**
   * Live-filter: navigate to the URL reflecting the current input values.
   * Text inputs debounce ~300ms so we don't fire on every keystroke; selects,
   * dates and the checkbox call this with `immediate=true` for instant feedback.
   */
  function pushFilters(immediate = false) {
    if (pending) clearTimeout(pending);
    const apply = () => {
      pending = null;
      const sp = new URLSearchParams();
      if (search) sp.set('search', search);
      if (status) sp.set('status', status);
      if (bookId) sp.set('book_id', bookId);
      if (startDate) sp.set('start_date', startDate);
      if (endDate) sp.set('end_date', endDate);
      if (includeLow) sp.set('include_low_amount', 'true');
      sp.set('page', '1');
      goto(`?${sp.toString()}`, { keepFocus: true, noScroll: true, replaceState: true });
    };
    if (immediate) apply();
    else pending = setTimeout(apply, 300);
  }

  function resetFilters() {
    if (pending) {
      clearTimeout(pending);
      pending = null;
    }
    search = '';
    status = '';
    bookId = '';
    startDate = '';
    endDate = '';
    includeLow = false;
    goto('?', { keepFocus: true, noScroll: true, replaceState: true });
  }

  const hasActiveFilters = $derived(
    Boolean(search || status || bookId || startDate || endDate || includeLow)
  );

  function gotoPage(p: number) {
    const sp = new URLSearchParams(data.currentSearch);
    sp.set('page', String(p));
    goto(`?${sp.toString()}`, { keepFocus: true, noScroll: true });
  }

  const exportHref = $derived(buildExportUrl(data.filters));

  const formatCurrency = (n: number, ccy = 'XOF') =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: ccy,
      maximumFractionDigits: 0
    }).format(n);

  const formatDate = (iso: string) =>
    new Intl.DateTimeFormat('fr-FR', { dateStyle: 'short', timeStyle: 'short' }).format(
      new Date(iso)
    );

  // Semantic status vocabulary. Soft pills for the everyday states; the
  // anomaly (security_error) is a solid alert pill so the fraud signal stands
  // out from a plain "Échouée". Fallback uses the warm neutral token, never a
  // cool slate (off-palette).
  function statusBadge(s: string) {
    const map = {
      SUCCESS: {
        icon: CheckCircle2,
        color: 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-600/20',
        label: 'Payée'
      },
      PENDING: {
        icon: Clock,
        color: 'bg-amber-50 text-amber-700 ring-1 ring-amber-600/20',
        label: 'En attente'
      },
      FAILED: {
        icon: XCircle,
        color: 'bg-red-50 text-red-700 ring-1 ring-red-600/20',
        label: 'Échouée'
      },
      SECURITY_ERROR: {
        icon: AlertCircle,
        color: 'bg-destructive text-destructive-foreground',
        label: 'Anomalie'
      }
    } as const;
    return (
      map[s as keyof typeof map] ?? {
        icon: AlertCircle,
        color: 'bg-muted text-muted-foreground ring-1 ring-border',
        label: s
      }
    );
  }

  // Focus the provider-id field when the sync drawer opens.
  $effect(() => {
    if (syncingId) tick().then(() => document.getElementById('ptx')?.focus());
  });

  function canResend(t: ApiTransaction): boolean {
    return t.status === 'SUCCESS';
  }

  function canSync(t: ApiTransaction): boolean {
    return t.status === 'PENDING' || t.status === 'FAILED';
  }
</script>

<svelte:head>
  <title>Transactions · CaaS</title>
</svelte:head>

<header class="mb-6 flex items-center justify-between">
  <div>
    <h1 class="text-2xl font-semibold tracking-tight">Transactions</h1>
    <p class="text-muted-foreground mt-1 text-sm">
      {data.result.total.toLocaleString('fr-FR')} résultat{data.result.total > 1 ? 's' : ''} · page
      {data.result.page} / {Math.max(1, data.result.pages)}
    </p>
  </div>
  <a href={exportHref} download class={buttonVariants({ variant: 'outline' })}>
    <Download class="h-4 w-4" /> Exporter (xlsx)
  </a>
</header>

<Card class="mb-4 p-4">
  <!-- Live filter: every change triggers `pushFilters` directly. Text inputs
       debounce, selects / dates / checkbox apply immediately. Form has
       `onsubmit prevent` only as a safety net for Enter key. -->
  <form class="grid grid-cols-1 gap-3 md:grid-cols-12" onsubmit={(e) => e.preventDefault()}>
    <div class="space-y-1 md:col-span-4">
      <Label for="t-search" class="text-xs">Recherche (email, nom, ID)</Label>
      <div class="relative">
        <Search
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
        />
        <Input
          id="t-search"
          bind:value={search}
          oninput={() => pushFilters()}
          placeholder="Rechercher…"
          class="pl-9"
        />
      </div>
    </div>

    <div class="space-y-1 md:col-span-2">
      <Label for="t-status" class="text-xs">Statut</Label>
      <Combobox
        id="t-status"
        bind:value={status}
        options={STATUS_OPTIONS}
        emptyLabel="Tous"
        placeholder="Filtrer un statut…"
        onchange={() => pushFilters(true)}
      />
    </div>

    <div class="space-y-1 md:col-span-2">
      <Label for="t-book" class="text-xs">Produit</Label>
      <Input
        id="t-book"
        bind:value={bookId}
        oninput={() => pushFilters()}
        placeholder="lutte-contre-fraude"
      />
    </div>

    <div class="space-y-1 md:col-span-2">
      <Label for="t-start" class="text-xs">Du</Label>
      <Input id="t-start" type="date" bind:value={startDate} onchange={() => pushFilters(true)} />
    </div>

    <div class="space-y-1 md:col-span-2">
      <Label for="t-end" class="text-xs">Au</Label>
      <Input id="t-end" type="date" bind:value={endDate} onchange={() => pushFilters(true)} />
    </div>

    <div class="col-span-full flex items-center justify-between">
      <label class="flex items-center gap-2 text-sm">
        <input
          type="checkbox"
          bind:checked={includeLow}
          onchange={() => pushFilters(true)}
          class="border-input h-4 w-4 rounded"
        />
        Inclure les petits montants
      </label>
      {#if hasActiveFilters}
        <Button type="button" variant="ghost" size="sm" onclick={resetFilters}>
          <X class="h-3.5 w-3.5" /> Effacer les filtres
        </Button>
      {/if}
    </div>
  </form>
</Card>

{#if form?.error}
  <div
    class="border-destructive/30 bg-destructive/5 text-destructive mb-4 rounded-md border p-3 text-sm"
  >
    {form.error}
  </div>
{/if}

{#if data.result.items.length === 0}
  <Card class="p-12 text-center">
    <div class="bg-muted mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full">
      <Search class="text-muted-foreground h-5 w-5" />
    </div>
    <p class="font-medium">Aucune transaction</p>
    <p class="text-muted-foreground mx-auto mt-1 max-w-sm text-sm">
      {hasActiveFilters
        ? 'Aucun résultat pour ces filtres. Élargis la recherche ou efface-les.'
        : 'Les paiements apparaîtront ici dès la première transaction.'}
    </p>
    {#if hasActiveFilters}
      <Button type="button" variant="outline" size="sm" class="mt-4" onclick={resetFilters}>
        <X class="h-3.5 w-3.5" /> Effacer les filtres
      </Button>
    {/if}
  </Card>
{:else}
  <Card
    class={cn(
      'overflow-x-auto transition-opacity duration-200 motion-reduce:transition-none',
      navigating.to && 'pointer-events-none opacity-60'
    )}
  >
    <table class="w-full text-sm">
      <thead class="bg-muted/30 text-muted-foreground border-b text-xs uppercase">
        <tr>
          <th class="px-3 py-2.5 text-left font-medium">Date</th>
          <th class="px-3 py-2.5 text-left font-medium">Client</th>
          <th class="px-3 py-2.5 text-left font-medium">Produit</th>
          <th class="px-3 py-2.5 text-right font-medium">Montant</th>
          <th class="px-3 py-2.5 text-left font-medium">Statut</th>
          <th class="px-3 py-2.5 text-right font-medium">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y">
        {#each data.result.items as t (t.id)}
          {@const b = statusBadge(t.status)}
          {@const Icon = b.icon}
          <tr class="hover:bg-muted/30">
            <td class="text-muted-foreground px-3 py-2.5 align-top text-xs">
              {formatDate(t.created_at)}
            </td>
            <td class="px-3 py-2.5">
              <p class="font-medium">{t.user_name ?? '—'}</p>
              <p class="text-muted-foreground text-xs">{t.user_email}</p>
              {#if t.user_phone}
                <p class="text-muted-foreground text-xs">{t.user_phone}</p>
              {/if}
            </td>
            <td class="px-3 py-2.5">
              <code class="bg-muted rounded px-1.5 py-0.5 text-xs">{t.book_id ?? '—'}</code>
            </td>
            <td class="px-3 py-2.5 text-right font-medium">
              {formatCurrency(t.amount, t.currency)}
            </td>
            <td class="px-3 py-2.5">
              <span
                class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium {b.color}"
              >
                <Icon class="h-3 w-3" />
                {b.label}
              </span>
              {#if t.transaction_id}
                <p class="text-muted-foreground mt-0.5 text-[10px]">{t.transaction_id}</p>
              {/if}
            </td>
            <td class="px-3 py-2.5 text-right">
              <div class="flex justify-end gap-1">
                {#if canResend(t)}
                  <form method="POST" action="?/resend" use:enhance>
                    <input type="hidden" name="id" value={t.id} />
                    <button
                      type="submit"
                      aria-label="Renvoyer l'email"
                      title="Renvoyer l'email de livraison"
                      class="text-muted-foreground hover:bg-accent hover:text-accent-foreground focus-visible:ring-ring flex h-8 w-8 items-center justify-center rounded-md transition-colors focus-visible:ring-2 focus-visible:outline-none"
                    >
                      <MailCheck class="h-4 w-4" />
                    </button>
                  </form>
                {/if}
                {#if canSync(t)}
                  <button
                    type="button"
                    onclick={() => (syncingId = t.id)}
                    aria-label="Synchroniser"
                    title="Synchroniser avec le provider"
                    class="text-muted-foreground hover:bg-accent hover:text-accent-foreground focus-visible:ring-ring flex h-8 w-8 items-center justify-center rounded-md transition-colors focus-visible:ring-2 focus-visible:outline-none"
                  >
                    <RefreshCw class="h-4 w-4" />
                  </button>
                {/if}
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </Card>

  {#if data.result.pages > 1}
    <div class="mt-4 flex items-center justify-between">
      <p class="text-muted-foreground text-xs">
        Affichage de {(data.result.page - 1) * data.result.size + 1}–{Math.min(
          data.result.page * data.result.size,
          data.result.total
        )} sur {data.result.total}
      </p>
      <div class="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={data.result.page <= 1}
          onclick={() => gotoPage(data.result.page - 1)}
        >
          <ChevronLeft class="h-3.5 w-3.5" /> Précédent
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={data.result.page >= data.result.pages}
          onclick={() => gotoPage(data.result.page + 1)}
        >
          Suivant <ChevronRight class="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  {/if}
{/if}

<Drawer
  open={syncingId !== null}
  title="Synchroniser la transaction"
  description="Force la vérification du paiement auprès du provider."
  onclose={() => (syncingId = null)}
>
  {#if syncTarget}
    <div class="border-border bg-muted/40 mb-4 rounded-md border p-3">
      <p class="text-sm font-medium">{syncTarget.user_email}</p>
      <p class="text-muted-foreground mt-0.5 text-xs">
        Montant {formatCurrency(syncTarget.amount, syncTarget.currency)} · {formatDate(
          syncTarget.created_at
        )}
      </p>
    </div>
  {/if}

  <form
    id="sync-form"
    method="POST"
    action="?/sync"
    use:enhance={() => {
      syncing = true;
      return async ({ result, update }) => {
        await update();
        syncing = false;
        // Keep the drawer open on validation failure so the user can retry.
        if (result.type !== 'failure') syncingId = null;
      };
    }}
    class="space-y-3"
  >
    <input type="hidden" name="id" value={syncingId} />
    <div class="space-y-1.5">
      <Label for="ptx">Identifiant transaction (provider)</Label>
      <Input
        id="ptx"
        name="provider_tx_id"
        required
        autocomplete="off"
        placeholder="Ex. 123456789"
      />
      <p class="text-muted-foreground text-xs">
        L'identifiant Kkiapay (<code class="bg-muted rounded px-1 py-0.5">transactionId</code>)
        renvoyé au paiement.
      </p>
    </div>
    {#if form?.error}
      <p
        class="border-destructive/30 bg-destructive/5 text-destructive rounded-md border p-2 text-sm"
      >
        {form.error}
      </p>
    {/if}
  </form>

  {#snippet footer()}
    <div class="flex items-center justify-end gap-2">
      <Button type="button" variant="outline" onclick={() => (syncingId = null)}>Annuler</Button>
      <Button type="submit" form="sync-form" disabled={syncing}>
        <RefreshCw class={cn('h-4 w-4', syncing && 'animate-spin')} />
        {syncing ? 'Synchronisation…' : 'Synchroniser'}
      </Button>
    </div>
  {/snippet}
</Drawer>
