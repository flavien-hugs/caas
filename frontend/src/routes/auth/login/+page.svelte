<script lang="ts">
  import { enhance } from '$app/forms';
  import {
    Mail,
    Lock,
    Eye,
    EyeOff,
    Store,
    CreditCard,
    Wallet,
    Coins,
    Banknote,
    ShoppingBag,
    Smartphone,
    ShieldCheck,
    Receipt,
    Send,
    TrendingUp
  } from 'lucide-svelte';
  import { Button, Card, Input, Label } from '$lib/components/ui';
  import type { ActionData } from './$types';

  let { form }: { form: ActionData } = $props();
  let submitting = $state(false);
  let showPassword = $state(false);

  // Decorative background icons (commerce / paiement). Spread around the edges,
  // away from the centre where the card sits. Purely cosmetic — aria-hidden.
  const FLOATERS = [
    { icon: CreditCard, top: '12%', left: '8%', size: 56, delay: 0, dur: 9 },
    { icon: Wallet, top: '72%', left: '11%', size: 46, delay: 1.5, dur: 11 },
    { icon: Coins, top: '20%', left: '86%', size: 52, delay: 0.8, dur: 10 },
    { icon: ShoppingBag, top: '80%', left: '84%', size: 48, delay: 2.2, dur: 12 },
    { icon: Smartphone, top: '46%', left: '4%', size: 38, delay: 1.1, dur: 9.5 },
    { icon: Banknote, top: '14%', left: '58%', size: 42, delay: 2.8, dur: 13 },
    { icon: ShieldCheck, top: '58%', left: '92%', size: 44, delay: 0.4, dur: 10.5 },
    { icon: Receipt, top: '86%', left: '46%', size: 36, delay: 1.9, dur: 11.5 },
    { icon: Send, top: '8%', left: '34%', size: 34, delay: 3.1, dur: 12.5 },
    { icon: TrendingUp, top: '52%', left: '72%', size: 40, delay: 0.6, dur: 9.8 }
  ];
</script>

<svelte:head>
  <title>Connexion · CaaS</title>
</svelte:head>

<div
  class="via-background relative flex min-h-screen items-center justify-center overflow-hidden bg-gradient-to-b from-amber-50 to-orange-50/40 px-6"
>
  <!-- Background ambiance -->
  <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
    <!-- Soft colour glows -->
    <div
      class="glow absolute -top-24 -left-24 h-96 w-96 rounded-full bg-amber-300/30 blur-3xl"
    ></div>
    <div
      class="glow absolute -right-24 -bottom-24 h-[28rem] w-[28rem] rounded-full bg-orange-400/20 blur-3xl"
      style="animation-delay:2.5s"
    ></div>

    <!-- Floating icons -->
    {#each FLOATERS as f, i (i)}
      {@const Icon = f.icon}
      <span
        class="floaty absolute {i % 3 === 0 ? 'text-orange-400/20' : 'text-amber-500/15'}"
        style="top:{f.top};left:{f.left};--dur:{f.dur}s;--delay:{f.delay}s"
      >
        <Icon size={f.size} strokeWidth={1.5} />
      </span>
    {/each}
  </div>

  <!-- Login card -->
  <div class="rise relative z-10 w-full max-w-sm">
    <Card class="bg-card/90 border-border/60 p-8 shadow-xl shadow-orange-900/5 backdrop-blur-sm">
      <header class="mb-6 text-center">
        <div class="mb-4 flex justify-center">
          <div
            class="badge-pop flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-amber-400 via-orange-500 to-orange-600 shadow-lg shadow-orange-500/30"
          >
            <Store class="h-7 w-7 text-white" />
          </div>
        </div>
        <h1 class="text-xl font-semibold tracking-tight">CaaS Admin</h1>
        <p class="text-muted-foreground mt-1 text-sm">Connexion à l'espace d'administration.</p>
      </header>

      <form
        method="POST"
        use:enhance={() => {
          submitting = true;
          return async ({ update }) => {
            await update();
            submitting = false;
          };
        }}
        class="space-y-4"
      >
        <div class="space-y-2">
          <Label for="email">Email</Label>
          <div class="group relative">
            <Mail
              class="text-muted-foreground group-focus-within:text-primary pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 transition-colors"
            />
            <Input
              id="email"
              name="email"
              type="email"
              autocomplete="email"
              inputmode="email"
              placeholder="vous@exemple.com"
              required
              class="pl-9"
              value={form?.email ?? ''}
            />
          </div>
        </div>

        <div class="space-y-2">
          <Label for="password">Mot de passe</Label>
          <div class="group relative">
            <Lock
              class="text-muted-foreground group-focus-within:text-primary pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 transition-colors"
            />
            <Input
              id="password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autocomplete="current-password"
              placeholder="••••••••"
              required
              class="pr-10 pl-9"
            />
            <button
              type="button"
              onclick={() => (showPassword = !showPassword)}
              aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
              aria-pressed={showPassword}
              class="text-muted-foreground hover:bg-secondary hover:text-foreground focus-visible:ring-ring absolute top-1/2 right-2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md transition-colors focus-visible:ring-2 focus-visible:outline-none"
            >
              {#if showPassword}
                <EyeOff class="h-4 w-4" />
              {:else}
                <Eye class="h-4 w-4" />
              {/if}
            </button>
          </div>
        </div>

        {#if form?.error}
          <p class="text-destructive text-sm">{form.error}</p>
        {/if}

        <Button type="submit" class="w-full" disabled={submitting}>
          {submitting ? 'Connexion…' : 'Se connecter'}
        </Button>
      </form>
    </Card>
  </div>

  <p class="text-muted-foreground/70 absolute bottom-5 z-10 text-xs">
    Paiement mobile money · Afrique francophone
  </p>
</div>

<style>
  @keyframes floaty {
    0%,
    100% {
      transform: translateY(0) rotate(0deg);
    }
    50% {
      transform: translateY(-18px) rotate(6deg);
    }
  }
  @keyframes rise {
    from {
      opacity: 0;
      transform: translateY(18px) scale(0.98);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
  @keyframes glow {
    0%,
    100% {
      opacity: 0.55;
      transform: scale(1);
    }
    50% {
      opacity: 0.85;
      transform: scale(1.12);
    }
  }
  @keyframes badgePop {
    from {
      opacity: 0;
      transform: scale(0.6) rotate(-12deg);
    }
    to {
      opacity: 1;
      transform: scale(1) rotate(0deg);
    }
  }

  .floaty {
    animation: floaty var(--dur, 10s) ease-in-out infinite;
    animation-delay: var(--delay, 0s);
  }
  .glow {
    animation: glow 8s ease-in-out infinite;
  }
  .rise {
    animation: rise 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
  }
  .badge-pop {
    animation: badgePop 0.7s cubic-bezier(0.34, 1.56, 0.64, 1) 0.1s both;
  }

  @media (prefers-reduced-motion: reduce) {
    .floaty,
    .glow,
    .rise,
    .badge-pop {
      animation: none;
    }
  }
</style>
