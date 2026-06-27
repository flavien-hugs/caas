<script lang="ts">
  import { enhance } from '$app/forms';
  import { buttonVariants } from '$lib/components/ui';
  import { cn } from '$lib/utils';
  import { outerClasses, StyleProps } from './style';
  import type { PaymentFormProps } from './types';

  interface Props {
    props: PaymentFormProps;
    mode?: 'edit' | 'preview';
    /** Form action payload (errors + last submitted values). Provided
     *  by ``/p/[slug]/+page.svelte`` when the parent page wires it. */
    form?: { error?: string; form?: Record<string, string> } | null;
  }

  let { props, mode = 'preview', form = null }: Props = $props();

  let submitting = $state(false);
  const f = $derived(form?.form ?? {});
  const editDisabled = $derived(mode === 'edit');

  const fieldClass =
    'border-input bg-background focus-visible:ring-ring h-9 w-full rounded-md border px-3 text-sm shadow-sm focus-visible:ring-2 focus-visible:outline-none disabled:opacity-50';

  // Section-level style (background / padding) shared with the other blocks
  // via the ``_style`` blob and ``outerClasses``.
  const style = $derived(StyleProps.parse((props as Record<string, unknown>)._style ?? {}));
  const sectionClass = $derived(outerClasses(style));

  // Card-level appearance, driven by the block props.
  const WIDTHS = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-lg' } as const;
  const CARD_BG = { card: 'bg-card', muted: 'bg-muted/40', accent: 'bg-accent' } as const;
  const heading = $derived(props.title || 'Finaliser votre commande');
  const wrapClass = $derived(
    cn(
      'w-full',
      WIDTHS[props.width ?? 'md'],
      props.align === 'left' ? 'mr-auto ml-0' : 'mx-auto',
      props.variant === 'plain'
        ? ''
        : cn(
            'text-foreground rounded-lg border p-6 shadow-sm',
            CARD_BG[props.cardBackground ?? 'card']
          )
    )
  );
  const ctaClass = $derived(
    cn(buttonVariants({ variant: props.ctaVariant ?? 'default', size: 'lg' }), 'w-full')
  );
</script>

<section id="payment" class={sectionClass}>
  <div class={wrapClass}>
    {#if heading}
      <h2 class="text-lg font-semibold">{heading}</h2>
    {/if}
    {#if props.amountHint}
      <p class="text-muted-foreground mt-1 text-sm">{props.amountHint}</p>
    {/if}

    <form
      method="POST"
      action="?/checkout"
      use:enhance={({ cancel }) => {
        if (editDisabled) {
          cancel();
          return;
        }
        submitting = true;
        return async ({ update }) => {
          await update();
          submitting = false;
        };
      }}
      class="mt-4 space-y-3"
    >
      <input type="hidden" name="book_id" value={props.bookId} />

      <div class="grid grid-cols-2 gap-3">
        <input
          type="text"
          name="name"
          required
          placeholder="Prénom"
          value={f.name ?? ''}
          disabled={editDisabled}
          class={fieldClass}
        />
        <input
          type="text"
          name="surname"
          required
          placeholder="Nom"
          value={f.surname ?? ''}
          disabled={editDisabled}
          class={fieldClass}
        />
      </div>

      <input
        type="email"
        name="email"
        required
        placeholder="vous@exemple.com"
        value={f.email ?? ''}
        disabled={editDisabled}
        class={fieldClass}
      />

      <input
        type="tel"
        name="phone"
        required
        placeholder="Téléphone (+225…)"
        value={f.phone ?? ''}
        disabled={editDisabled}
        class={fieldClass}
      />

      <div class="grid grid-cols-2 gap-3">
        <input
          type="text"
          name="city"
          required
          placeholder="Ville"
          value={f.city ?? ''}
          disabled={editDisabled}
          class={fieldClass}
        />
        <input
          type="text"
          name="country"
          required
          placeholder="Pays"
          value={f.country ?? 'Côte d’Ivoire'}
          disabled={editDisabled}
          class={fieldClass}
        />
      </div>

      {#if form?.error}
        <p class="text-destructive text-sm">{form.error}</p>
      {/if}

      <button type="submit" disabled={submitting || editDisabled} class={ctaClass}>
        {submitting ? 'Patientez…' : props.ctaLabel || 'Payer maintenant'}
      </button>
    </form>

    {#if editDisabled}
      <p class="text-muted-foreground mt-3 text-center text-xs">
        Prévisualisation — formulaire désactivé en édition.
      </p>
    {/if}
  </div>
</section>
