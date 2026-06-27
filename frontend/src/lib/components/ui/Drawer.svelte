<script lang="ts">
  import { X } from 'lucide-svelte';
  import { cn } from '$lib/utils';

  interface Props {
    open: boolean;
    title?: string;
    description?: string;
    /** Tailwind width class for the panel. Defaults to ``max-w-md``. */
    width?: string;
    onclose?: () => void;
    children: import('svelte').Snippet;
    /** Optional footer slot for the action bar (Cancel / Confirm). */
    footer?: import('svelte').Snippet;
  }

  let {
    open = $bindable(false),
    title,
    description,
    width = 'max-w-md',
    onclose,
    children,
    footer
  }: Props = $props();

  function close() {
    open = false;
    onclose?.();
  }

  // Lock the page scroll while the drawer is open so the underlying list
  // doesn't slide around when the user scrolls within the drawer.
  $effect(() => {
    if (open) {
      const previous = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
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
  <!-- Backdrop -->
  <div
    class="fixed inset-0 z-40 bg-black/30 transition-opacity"
    onclick={close}
    role="presentation"
    aria-hidden="true"
  ></div>

  <!-- Sliding panel -->
  <!-- svelte-ignore a11y_no_noninteractive_element_to_interactive_role -->
  <aside
    class={cn('bg-background fixed inset-y-0 right-0 z-50 flex w-full flex-col shadow-xl', width)}
    role="dialog"
    aria-modal="true"
    aria-labelledby={title ? 'drawer-title' : undefined}
  >
    {#if title || description}
      <header class="flex shrink-0 items-start justify-between gap-3 border-b px-4 py-3">
        <div class="min-w-0">
          {#if title}
            <h2 id="drawer-title" class="text-base font-semibold tracking-tight">{title}</h2>
          {/if}
          {#if description}
            <p class="text-muted-foreground mt-0.5 text-xs">{description}</p>
          {/if}
        </div>
        <button
          type="button"
          aria-label="Fermer"
          onclick={close}
          class="text-muted-foreground hover:bg-secondary hover:text-foreground flex h-7 w-7 shrink-0 items-center justify-center rounded-md"
        >
          <X class="h-4 w-4" />
        </button>
      </header>
    {/if}

    <div class="flex-1 overflow-y-auto p-4">
      {@render children()}
    </div>

    {#if footer}
      <footer class="bg-muted/30 shrink-0 border-t px-4 py-3">
        {@render footer()}
      </footer>
    {/if}
  </aside>
{/if}
