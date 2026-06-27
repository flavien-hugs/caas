<script lang="ts">
  import { ChevronsUpDown, Check, X } from 'lucide-svelte';
  import { cn } from '$lib/utils';

  export interface ComboboxOption {
    value: string;
    label: string;
    description?: string;
  }

  interface Props {
    id?: string;
    /** When set, renders a hidden ``<input>`` with this name so the value is
     *  submitted with the surrounding form. */
    name?: string;
    value: string;
    options: ComboboxOption[];
    placeholder?: string;
    /** Shown when the input is empty AND no value is selected. */
    emptyLabel?: string;
    /** Allow clearing the selection (shows an × button). */
    clearable?: boolean;
    disabled?: boolean;
    /** ``sm`` = ``h-8 text-xs``, suitable for dense inspector panes. */
    size?: 'default' | 'sm';
    class?: string;
    onchange?: (value: string) => void;
  }

  let {
    id,
    name,
    value = $bindable(''),
    options,
    placeholder = 'Rechercher…',
    emptyLabel = 'Tous',
    clearable = true,
    disabled = false,
    size = 'default',
    class: className = '',
    onchange
  }: Props = $props();

  const triggerSize = $derived(size === 'sm' ? 'h-8 px-2 text-xs' : 'h-9 px-3 text-sm');

  let open = $state(false);
  let query = $state('');
  let highlight = $state(0);
  let rootEl: HTMLDivElement;
  let inputEl: HTMLInputElement | undefined = $state();

  const selected = $derived(options.find((o) => o.value === value) ?? null);
  const displayedLabel = $derived(selected?.label ?? '');

  const filtered = $derived(
    query.trim()
      ? options.filter((o) => o.label.toLowerCase().includes(query.toLowerCase()))
      : options
  );

  function openMenu() {
    if (disabled) return;
    open = true;
    query = '';
    highlight = Math.max(
      0,
      filtered.findIndex((o) => o.value === value)
    );
    // Defer focus to next tick so the input is in the DOM.
    queueMicrotask(() => inputEl?.focus());
  }

  function closeMenu() {
    open = false;
    query = '';
  }

  function select(opt: ComboboxOption) {
    value = opt.value;
    onchange?.(value);
    closeMenu();
  }

  function clear(e: Event) {
    e.stopPropagation();
    if (!clearable) return;
    value = '';
    onchange?.(value);
  }

  function handleKey(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      closeMenu();
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      highlight = Math.min(filtered.length - 1, highlight + 1);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      highlight = Math.max(0, highlight - 1);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[highlight]) select(filtered[highlight]);
    }
  }

  /** Close when the user clicks anywhere outside the root. */
  function handleDocClick(e: MouseEvent) {
    if (!open) return;
    if (rootEl && !rootEl.contains(e.target as Node)) closeMenu();
  }

  $effect(() => {
    if (open) {
      document.addEventListener('mousedown', handleDocClick);
      return () => document.removeEventListener('mousedown', handleDocClick);
    }
  });

  // Re-clamp highlight whenever the filtered list shrinks past it.
  $effect(() => {
    if (highlight >= filtered.length) highlight = Math.max(0, filtered.length - 1);
  });
</script>

<div bind:this={rootEl} class={cn('relative', className)}>
  {#if name}
    <input type="hidden" {name} {value} />
  {/if}
  <button
    {id}
    type="button"
    {disabled}
    onclick={() => (open ? closeMenu() : openMenu())}
    aria-haspopup="listbox"
    aria-expanded={open}
    class={cn(
      'border-input bg-background hover:border-foreground/20 focus-visible:ring-ring flex w-full items-center justify-between gap-2 rounded-md border text-left shadow-sm transition-colors focus-visible:ring-2 focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50',
      triggerSize,
      open && 'ring-ring ring-2'
    )}
  >
    <span class="min-w-0 truncate {value ? '' : 'text-muted-foreground'}">
      {displayedLabel || emptyLabel}
    </span>
    <span class="flex shrink-0 items-center gap-1">
      {#if clearable && value}
        <span
          role="button"
          tabindex="-1"
          aria-label="Effacer"
          onclick={clear}
          onkeydown={(e) => e.key === 'Enter' && clear(e)}
          class="text-muted-foreground hover:bg-muted hover:text-foreground flex h-5 w-5 items-center justify-center rounded"
        >
          <X class="h-3 w-3" />
        </span>
      {/if}
      <ChevronsUpDown class="text-muted-foreground h-3.5 w-3.5" />
    </span>
  </button>

  {#if open}
    <div
      class="bg-popover absolute top-full right-0 left-0 z-50 mt-1 max-h-72 overflow-hidden rounded-md border shadow-lg"
      role="dialog"
    >
      <div class="border-b p-2">
        <input
          bind:this={inputEl}
          type="text"
          bind:value={query}
          onkeydown={handleKey}
          {placeholder}
          class="h-7 w-full rounded border-0 bg-transparent px-1 text-sm focus:ring-0 focus:outline-none"
          autocomplete="off"
        />
      </div>
      <ul role="listbox" class="max-h-60 overflow-y-auto p-1">
        {#if filtered.length === 0}
          <li class="text-muted-foreground px-2 py-2 text-xs">Aucun résultat.</li>
        {/if}
        {#each filtered as opt, i (opt.value)}
          {@const isSelected = opt.value === value}
          {@const isHighlighted = i === highlight}
          <li>
            <button
              type="button"
              role="option"
              aria-selected={isSelected}
              onmousedown={(e) => e.preventDefault()}
              onclick={() => select(opt)}
              onmouseenter={() => (highlight = i)}
              class={cn(
                'flex w-full items-center justify-between gap-2 rounded px-2 py-1.5 text-left text-sm',
                isHighlighted && 'bg-secondary',
                isSelected && 'font-medium'
              )}
            >
              <span class="min-w-0">
                <span class="block truncate">{opt.label}</span>
                {#if opt.description}
                  <span class="text-muted-foreground block truncate text-xs">{opt.description}</span
                  >
                {/if}
              </span>
              {#if isSelected}
                <Check class="text-primary h-3.5 w-3.5 shrink-0" />
              {/if}
            </button>
          </li>
        {/each}
      </ul>
    </div>
  {/if}
</div>
