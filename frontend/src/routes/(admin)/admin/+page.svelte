<script lang="ts">
  import { Card } from '$lib/components/ui';
  import { Receipt, Wallet, TrendingUp, AlertCircle } from 'lucide-svelte';

  let { data } = $props();

  const formatCurrency = (n: number) =>
    new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'XOF',
      maximumFractionDigits: 0
    }).format(n);

  const formatNumber = (n: number) => new Intl.NumberFormat('fr-FR').format(n);
</script>

<svelte:head>
  <title>Tableau de bord · CaaS</title>
</svelte:head>

<header class="mb-8">
  <h1 class="text-2xl font-semibold tracking-tight">Tableau de bord</h1>
  <p class="text-muted-foreground mt-1 text-sm">Vue d'ensemble des paiements et de l'activité.</p>
</header>

{#if data.forbidden}
  <Card class="border-amber-200 bg-amber-50 p-6">
    <div class="flex items-start gap-3">
      <AlertCircle class="mt-0.5 h-5 w-5 text-amber-600" />
      <div>
        <p class="font-medium">Accès restreint</p>
        <p class="text-muted-foreground mt-1 text-sm">
          Ton rôle ne permet pas d'afficher ces statistiques.
        </p>
      </div>
    </div>
  </Card>
{:else if data.stats}
  {@const s = data.stats}
  {@const successRate =
    s.total_transactions > 0 ? Math.round((s.successful_sales / s.total_transactions) * 100) : null}
  <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
    <Card class="p-5">
      <div class="flex items-center justify-between">
        <p class="text-muted-foreground text-sm">Transactions</p>
        <Receipt class="text-muted-foreground h-4 w-4" />
      </div>
      <p class="mt-2 text-2xl font-semibold">{formatNumber(s.total_transactions)}</p>
      <p class="text-muted-foreground mt-1 text-xs">
        {formatNumber(s.successful_sales)} réussies
      </p>
    </Card>

    <Card class="p-5">
      <div class="flex items-center justify-between">
        <p class="text-muted-foreground text-sm">Revenu total</p>
        <Wallet class="text-muted-foreground h-4 w-4" />
      </div>
      <p class="mt-2 text-2xl font-semibold">{formatCurrency(s.total_revenue)}</p>
      <p class="text-muted-foreground mt-1 text-xs">Hors transactions échouées</p>
    </Card>

    <Card class="p-5">
      <div class="flex items-center justify-between">
        <p class="text-muted-foreground text-sm">Taux de succès</p>
        <TrendingUp class="text-muted-foreground h-4 w-4" />
      </div>
      <p class="mt-2 text-2xl font-semibold">
        {successRate === null ? '—' : `${successRate} %`}
      </p>
      <p class="text-muted-foreground mt-1 text-xs">
        {formatNumber(s.failed_transactions)} échouées
      </p>
    </Card>

    <Card class="p-5">
      <div class="flex items-center justify-between">
        <p class="text-muted-foreground text-sm">En attente</p>
        <AlertCircle class="text-muted-foreground h-4 w-4" />
      </div>
      <p class="mt-2 text-2xl font-semibold">{formatNumber(s.pending_transactions)}</p>
      <p class="text-muted-foreground mt-1 text-xs">Paiements à réconcilier</p>
    </Card>
  </div>
{:else}
  <Card class="p-6">
    <p class="text-muted-foreground text-sm">Aucune donnée disponible.</p>
  </Card>
{/if}
