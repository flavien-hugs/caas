<script lang="ts">
  import Button from './Button.svelte';

  interface Props {
    open: boolean;
    title: string;
    description?: string;
    confirmLabel?: string;
    cancelLabel?: string;
    /** Confirm button uses the destructive variant (red). */
    destructive?: boolean;
    /** Disables the confirm button + shows a pending label. */
    loading?: boolean;
    /** When set, the confirm button submits the form with this id (so the
     *  caller drives the action via a real <form use:enhance>). */
    confirmForm?: string;
    onconfirm?: () => void;
    onclose?: () => void;
    /** Optional extra body (e.g. the hidden form that confirmForm points at). */
    children?: import('svelte').Snippet;
  }

  let {
    open = $bindable(false),
    title,
    description,
    confirmLabel = 'Confirmer',
    cancelLabel = 'Annuler',
    destructive = false,
    loading = false,
    confirmForm,
    onconfirm,
    onclose,
    children
  }: Props = $props();

  let cardEl = $state<HTMLDivElement | undefined>();

  function close() {
    open = false;
    onclose?.();
  }

  // Lock page scroll while open and land focus on the first action (Cancel,
  // the safe default for a destructive confirm).
  $effect(() => {
    if (open) {
      const previous = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      cardEl?.querySelector('button')?.focus();
      return () => {
        document.body.style.overflow = previous;
      };
    }
  });

  function onkeydown(e: KeyboardEvent) {
    if (open && e.key === 'Escape') close();
  }
</script>

<svelte:window {onkeydown} />

{#if open}
  <div
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    role="presentation"
    aria-hidden="true"
    onclick={(e) => e.target === e.currentTarget && close()}
  >
    <!-- Backdrop -->
    <div class="ad-backdrop absolute inset-0 bg-black/40"></div>

    <!-- Dialog -->
    <div
      bind:this={cardEl}
      class="ad-card bg-card relative z-10 w-full max-w-md rounded-lg border p-6 shadow-xl"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
    >
      <h2 id="confirm-title" class="text-base font-semibold tracking-tight">{title}</h2>
      {#if description}
        <p class="text-muted-foreground mt-1.5 text-sm">{description}</p>
      {/if}

      {@render children?.()}

      <div class="mt-6 flex justify-end gap-2">
        <Button type="button" variant="outline" onclick={close}>
          {cancelLabel}
        </Button>
        {#if confirmForm}
          <Button
            type="submit"
            form={confirmForm}
            variant={destructive ? 'destructive' : 'default'}
            disabled={loading}
          >
            {loading ? '…' : confirmLabel}
          </Button>
        {:else}
          <Button
            type="button"
            variant={destructive ? 'destructive' : 'default'}
            disabled={loading}
            onclick={onconfirm}
          >
            {loading ? '…' : confirmLabel}
          </Button>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  @keyframes ad-fade {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }
  @keyframes ad-pop {
    from {
      opacity: 0;
      transform: translateY(8px) scale(0.98);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }
  .ad-backdrop {
    animation: ad-fade 0.15s ease-out both;
  }
  .ad-card {
    animation: ad-pop 0.18s cubic-bezier(0.16, 1, 0.3, 1) both;
  }
  @media (prefers-reduced-motion: reduce) {
    .ad-backdrop,
    .ad-card {
      animation: none;
    }
  }
</style>
