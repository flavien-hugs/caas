<script lang="ts">
  import { Plus, X } from 'lucide-svelte';
  import { Button, Combobox, Input, Label, type ComboboxOption } from '$lib/components/ui';
  import { getBlockDef } from '$blocks/registry';
  import type {
    CTAButtonProps,
    DividerProps,
    FAQProps,
    FeatureGridProps,
    HeroProps,
    ImageProps,
    PaymentFormProps,
    RichTextProps,
    SectionProps,
    SpacerProps
  } from '$blocks/types';
  import type { StyleProps } from '$blocks/style';
  import type { BuilderStore } from './store.svelte';

  let { store }: { store: BuilderStore } = $props();

  const block = $derived(store.selectedBlock);
  const def = $derived(block ? getBlockDef(block.type) : null);

  function update(patch: Record<string, unknown>) {
    if (!block) return;
    store.updateBlockProps(block.id, { ...block.props, ...patch });
  }

  /** Read the current ``_style`` blob from the selected block's props
   *  (defaulting to an empty object). */
  const style = $derived(
    (block?.props as Record<string, unknown>)?._style as Partial<StyleProps> | undefined
  );

  function updateStyle(patch: Partial<StyleProps>) {
    if (!block) return;
    const next = { ...(style ?? {}), ...patch };
    store.updateBlockProps(block.id, { ...block.props, _style: next });
  }

  // Centralised option lists — keep label/description close to the source so
  // the inspector stays declarative.

  const HERO_BG_OPTS: ComboboxOption[] = [
    { value: 'light', label: 'Clair' },
    { value: 'dark', label: 'Sombre' },
    { value: 'gradient', label: 'Dégradé' }
  ];

  const CTA_VARIANT_OPTS: ComboboxOption[] = [
    { value: 'default', label: 'Primaire' },
    { value: 'secondary', label: 'Secondaire' },
    { value: 'outline', label: 'Contour' }
  ];

  const ALIGN_OPTS: ComboboxOption[] = [
    { value: 'left', label: 'Gauche' },
    { value: 'center', label: 'Centre' },
    { value: 'right', label: 'Droite' }
  ];

  const COLS_OPTS: ComboboxOption[] = [
    { value: '1', label: '1 colonne' },
    { value: '2', label: '2 colonnes' },
    { value: '3', label: '3 colonnes' },
    { value: '4', label: '4 colonnes' }
  ];

  const GAP_OPTS: ComboboxOption[] = [
    { value: 'none', label: 'Aucun' },
    { value: 'sm', label: 'Petit' },
    { value: 'md', label: 'Moyen' },
    { value: 'lg', label: 'Grand' }
  ];

  const LAYOUT_OPTS: ComboboxOption[] = [
    { value: 'equal', label: 'Colonnes égales' },
    { value: 'sidebar-left', label: 'Sidebar gauche', description: '1/3 – 2/3' },
    { value: 'sidebar-right', label: 'Sidebar droite', description: '2/3 – 1/3' }
  ];

  const VALIGN_OPTS: ComboboxOption[] = [
    { value: 'start', label: 'Haut' },
    { value: 'center', label: 'Centre' },
    { value: 'end', label: 'Bas' },
    { value: 'stretch', label: 'Étirer' }
  ];

  const IMG_FIT_OPTS: ComboboxOption[] = [
    { value: 'cover', label: 'Couvrir', description: 'Remplit, recadre' },
    { value: 'contain', label: 'Contenir', description: 'Tout afficher' }
  ];

  const IMG_ROUNDED_OPTS: ComboboxOption[] = [
    { value: 'none', label: 'Aucun' },
    { value: 'md', label: 'Moyen' },
    { value: 'lg', label: 'Grand' },
    { value: 'full', label: 'Cercle' }
  ];

  const IMG_MAXW_OPTS: ComboboxOption[] = [
    { value: 'sm', label: 'Petite' },
    { value: 'md', label: 'Moyenne' },
    { value: 'lg', label: 'Grande' },
    { value: 'xl', label: 'XL' },
    { value: 'full', label: 'Pleine largeur' }
  ];

  const SPACER_OPTS: ComboboxOption[] = [
    { value: 'xs', label: 'XS' },
    { value: 'sm', label: 'Petit' },
    { value: 'md', label: 'Moyen' },
    { value: 'lg', label: 'Grand' },
    { value: 'xl', label: 'XL' }
  ];

  const DIVIDER_VARIANT_OPTS: ComboboxOption[] = [
    { value: 'solid', label: 'Pleine' },
    { value: 'dashed', label: 'Pointillés longs' },
    { value: 'dotted', label: 'Pointillés' }
  ];

  const DIVIDER_COLOR_OPTS: ComboboxOption[] = [
    { value: 'muted', label: 'Discrète' },
    { value: 'foreground', label: 'Foncée' },
    { value: 'primary', label: 'Primaire' }
  ];

  const STYLE_BG_OPTS: ComboboxOption[] = [
    { value: 'none', label: 'Aucun' },
    { value: 'muted', label: 'Discret' },
    { value: 'card', label: 'Carte' },
    { value: 'primary', label: 'Primaire' },
    { value: 'dark', label: 'Sombre' },
    { value: 'gradient', label: 'Dégradé' }
  ];

  const STYLE_PY_OPTS: ComboboxOption[] = [
    { value: 'none', label: 'Aucun' },
    { value: 'sm', label: 'Petit' },
    { value: 'md', label: 'Moyen' },
    { value: 'lg', label: 'Grand' },
    { value: 'xl', label: 'XL' }
  ];

  const STYLE_PX_OPTS: ComboboxOption[] = [
    { value: 'none', label: 'Aucun' },
    { value: 'sm', label: 'Petit' },
    { value: 'md', label: 'Moyen' },
    { value: 'lg', label: 'Grand' }
  ];

  const STYLE_MAXW_OPTS: ComboboxOption[] = [
    { value: 'none', label: 'Aucune' },
    { value: 'narrow', label: 'Étroite' },
    { value: 'normal', label: 'Normale' },
    { value: 'wide', label: 'Large' },
    { value: 'full', label: 'Pleine' }
  ];

  const STYLE_TEXT_OPTS: ComboboxOption[] = [
    { value: 'inherit', label: 'Hérité' },
    { value: 'muted', label: 'Discrète' },
    { value: 'primary', label: 'Primaire' },
    { value: 'white', label: 'Blanc' }
  ];
</script>

<aside class="bg-muted/30 w-full shrink-0 overflow-y-auto border-l md:w-80">
  {#if !block || !def}
    <div class="flex h-full items-center justify-center p-6 text-center">
      <p class="text-muted-foreground text-sm">
        Sélectionne un bloc dans le canvas pour le configurer.
      </p>
    </div>
  {:else}
    <header class="bg-background border-b px-2 py-2">
      <p class="text-muted-foreground text-xs tracking-wide uppercase">Bloc</p>
      <h3 class="text-sm font-semibold">{def.label}</h3>
    </header>

    <div class="space-y-3 p-2">
      {#if block.type === 'hero'}
        {@const p = block.props as unknown as HeroProps}
        <div class="space-y-2">
          <Label for="hero-headline">Titre</Label>
          <Input
            id="hero-headline"
            value={p.headline ?? ''}
            oninput={(e) => update({ headline: e.currentTarget.value })}
          />
        </div>
        <div class="space-y-2">
          <Label for="hero-subheadline">Sous-titre</Label>
          <textarea
            id="hero-subheadline"
            value={p.subheadline ?? ''}
            oninput={(e) => update({ subheadline: e.currentTarget.value })}
            class="border-input bg-background flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm shadow-sm"
          ></textarea>
          <p class="text-muted-foreground text-xs">
            Markdown supporté (**gras**, *italique*, [lien](url)).
          </p>
        </div>
        <div class="space-y-2">
          <Label for="hero-cta-label">Libellé CTA</Label>
          <Input
            id="hero-cta-label"
            value={p.ctaLabel ?? ''}
            oninput={(e) => update({ ctaLabel: e.currentTarget.value })}
          />
        </div>
        <div class="space-y-2">
          <Label for="hero-cta-href">URL CTA</Label>
          <Input
            id="hero-cta-href"
            type="url"
            value={p.ctaHref ?? ''}
            oninput={(e) => update({ ctaHref: e.currentTarget.value })}
          />
        </div>
        <div class="space-y-2">
          <Label for="hero-bg">Fond</Label>
          <Combobox
            id="hero-bg"
            value={p.background ?? 'light'}
            options={HERO_BG_OPTS}
            clearable={false}
            onchange={(v) => update({ background: v })}
          />
        </div>
      {:else if block.type === 'feature_grid'}
        {@const p = block.props as unknown as FeatureGridProps}
        <div class="space-y-2">
          <Label for="fg-headline">Titre</Label>
          <Input
            id="fg-headline"
            value={p.headline ?? ''}
            oninput={(e) => update({ headline: e.currentTarget.value })}
          />
        </div>

        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <Label>Cartes</Label>
            <button
              type="button"
              onclick={() =>
                update({ items: [...(p.items ?? []), { title: 'Nouvelle carte', body: '' }] })}
              class="text-primary inline-flex items-center gap-1 text-xs hover:underline"
            >
              <Plus class="h-3 w-3" /> Ajouter
            </button>
          </div>

          {#each p.items ?? [] as item, i (i)}
            <div class="bg-background relative space-y-1.5 rounded-md border p-2.5">
              <button
                type="button"
                onclick={() => update({ items: p.items.filter((_, j) => j !== i) })}
                aria-label="Supprimer la carte"
                class="text-muted-foreground hover:text-destructive absolute top-1.5 right-1.5"
              >
                <X class="h-3.5 w-3.5" />
              </button>
              <Input
                value={item.title}
                placeholder="Titre"
                oninput={(e) =>
                  update({
                    items: p.items.map((it, j) =>
                      j === i ? { ...it, title: e.currentTarget.value } : it
                    )
                  })}
              />
              <textarea
                value={item.body ?? ''}
                placeholder="Description (Markdown supporté)"
                oninput={(e) =>
                  update({
                    items: p.items.map((it, j) =>
                      j === i ? { ...it, body: e.currentTarget.value } : it
                    )
                  })}
                class="border-input bg-background flex min-h-[60px] w-full rounded-md border px-3 py-2 text-sm"
              ></textarea>
            </div>
          {/each}
        </div>
      {:else if block.type === 'faq'}
        {@const p = block.props as unknown as FAQProps}
        <div class="space-y-2">
          <Label for="faq-headline">Titre</Label>
          <Input
            id="faq-headline"
            value={p.headline ?? ''}
            oninput={(e) => update({ headline: e.currentTarget.value })}
          />
        </div>

        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <Label>Questions</Label>
            <button
              type="button"
              onclick={() =>
                update({
                  items: [...(p.items ?? []), { question: 'Question…', answer: 'Réponse…' }]
                })}
              class="text-primary inline-flex items-center gap-1 text-xs hover:underline"
            >
              <Plus class="h-3 w-3" /> Ajouter
            </button>
          </div>

          {#each p.items ?? [] as item, i (i)}
            <div class="bg-background relative space-y-1.5 rounded-md border p-2.5">
              <button
                type="button"
                onclick={() => update({ items: p.items.filter((_, j) => j !== i) })}
                aria-label="Supprimer la question"
                class="text-muted-foreground hover:text-destructive absolute top-1.5 right-1.5"
              >
                <X class="h-3.5 w-3.5" />
              </button>
              <Input
                value={item.question}
                placeholder="Question"
                oninput={(e) =>
                  update({
                    items: p.items.map((it, j) =>
                      j === i ? { ...it, question: e.currentTarget.value } : it
                    )
                  })}
              />
              <textarea
                value={item.answer}
                placeholder="Réponse (Markdown supporté)"
                oninput={(e) =>
                  update({
                    items: p.items.map((it, j) =>
                      j === i ? { ...it, answer: e.currentTarget.value } : it
                    )
                  })}
                class="border-input bg-background flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm"
              ></textarea>
            </div>
          {/each}
        </div>
      {:else if block.type === 'cta_button'}
        {@const p = block.props as unknown as CTAButtonProps}
        <div class="space-y-2">
          <Label for="cta-label">Libellé</Label>
          <Input
            id="cta-label"
            value={p.label ?? ''}
            oninput={(e) => update({ label: e.currentTarget.value })}
          />
        </div>
        <div class="space-y-2">
          <Label for="cta-href">URL</Label>
          <Input
            id="cta-href"
            type="url"
            value={p.href ?? ''}
            oninput={(e) => update({ href: e.currentTarget.value })}
          />
        </div>
        <div class="space-y-2">
          <Label for="cta-variant">Style</Label>
          <Combobox
            id="cta-variant"
            value={p.variant ?? 'default'}
            options={CTA_VARIANT_OPTS}
            clearable={false}
            onchange={(v) => update({ variant: v })}
          />
        </div>
        <div class="space-y-2">
          <Label for="cta-align">Alignement</Label>
          <Combobox
            id="cta-align"
            value={p.align ?? 'center'}
            options={ALIGN_OPTS}
            clearable={false}
            onchange={(v) => update({ align: v })}
          />
        </div>
      {:else if block.type === 'rich_text'}
        {@const p = block.props as unknown as RichTextProps}
        <div class="space-y-2">
          <Label for="rt-md">Contenu (Markdown)</Label>
          <textarea
            id="rt-md"
            value={p.markdown ?? ''}
            oninput={(e) => update({ markdown: e.currentTarget.value })}
            class="border-input bg-background flex min-h-[220px] w-full rounded-md border px-3 py-2 font-mono text-sm shadow-sm"
          ></textarea>
          <p class="text-muted-foreground text-xs">
            **gras**, *italique*, ligne vide = paragraphe.
          </p>
        </div>
      {:else if block.type === 'payment_form'}
        {@const p = block.props as unknown as PaymentFormProps}
        <div class="space-y-2">
          <Label for="pf-book">Identifiant produit (book_id)</Label>
          <Input
            id="pf-book"
            value={p.bookId ?? ''}
            oninput={(e) => update({ bookId: e.currentTarget.value })}
          />
        </div>
        <div class="space-y-2">
          <Label for="pf-title">Titre du formulaire</Label>
          <Input
            id="pf-title"
            value={p.title ?? ''}
            placeholder="Finaliser votre commande"
            oninput={(e) => update({ title: e.currentTarget.value })}
          />
        </div>
        <div class="space-y-2">
          <Label for="pf-cta">Libellé du bouton</Label>
          <Input
            id="pf-cta"
            value={p.ctaLabel ?? ''}
            oninput={(e) => update({ ctaLabel: e.currentTarget.value })}
          />
        </div>
        <div class="space-y-2">
          <Label for="pf-hint">Indication de prix</Label>
          <Input
            id="pf-hint"
            value={p.amountHint ?? ''}
            oninput={(e) => update({ amountHint: e.currentTarget.value })}
          />
        </div>

        <p class="text-muted-foreground pt-1 text-xs font-medium">Apparence</p>
        <div class="space-y-2">
          <Label for="pf-variant">Style</Label>
          <Combobox
            id="pf-variant"
            value={p.variant ?? 'card'}
            options={[
              { value: 'card', label: 'Carte', description: 'Bordure + ombre' },
              { value: 'plain', label: 'Sans cadre', description: 'Intégré à la section' }
            ]}
            clearable={false}
            onchange={(v) => update({ variant: v })}
          />
        </div>
        <div class="space-y-2">
          <Label for="pf-cardbg">Fond de carte</Label>
          <Combobox
            id="pf-cardbg"
            value={p.cardBackground ?? 'card'}
            options={[
              { value: 'card', label: 'Blanc' },
              { value: 'muted', label: 'Discret' },
              { value: 'accent', label: 'Ambré clair' }
            ]}
            clearable={false}
            onchange={(v) => update({ cardBackground: v })}
          />
        </div>
        <div class="space-y-2">
          <Label for="pf-width">Largeur</Label>
          <Combobox
            id="pf-width"
            value={p.width ?? 'md'}
            options={[
              { value: 'sm', label: 'Étroite' },
              { value: 'md', label: 'Moyenne' },
              { value: 'lg', label: 'Large' }
            ]}
            clearable={false}
            onchange={(v) => update({ width: v })}
          />
        </div>
        <div class="space-y-2">
          <Label for="pf-align">Alignement</Label>
          <Combobox
            id="pf-align"
            value={p.align ?? 'center'}
            options={[
              { value: 'center', label: 'Centré' },
              { value: 'left', label: 'À gauche' }
            ]}
            clearable={false}
            onchange={(v) => update({ align: v })}
          />
        </div>
        <div class="space-y-2">
          <Label for="pf-cta-variant">Style du bouton</Label>
          <Combobox
            id="pf-cta-variant"
            value={p.ctaVariant ?? 'default'}
            options={CTA_VARIANT_OPTS}
            clearable={false}
            onchange={(v) => update({ ctaVariant: v })}
          />
        </div>
      {:else if block.type === 'section'}
        {@const p = block.props as unknown as SectionProps}
        <div class="space-y-2">
          <Label for="sec-cols">Nombre de colonnes</Label>
          <Combobox
            id="sec-cols"
            value={String(p.columns ?? 2)}
            options={COLS_OPTS}
            clearable={false}
            onchange={(v) => {
              const cols = Number(v);
              const current = (p.children ?? []) as unknown[][];
              const next = Array.from({ length: cols }, (_, i) => current[i] ?? []);
              update({ columns: cols, children: next });
            }}
          />
        </div>
        <div class="space-y-2">
          <Label for="sec-gap">Espacement entre colonnes</Label>
          <Combobox
            id="sec-gap"
            value={p.gap ?? 'md'}
            options={GAP_OPTS}
            clearable={false}
            onchange={(v) => update({ gap: v })}
          />
        </div>
        {#if (p.columns ?? 2) === 2}
          <div class="space-y-2">
            <Label for="sec-layout">Disposition</Label>
            <Combobox
              id="sec-layout"
              value={p.layout ?? 'equal'}
              options={LAYOUT_OPTS}
              clearable={false}
              onchange={(v) => update({ layout: v })}
            />
          </div>
        {/if}
        <div class="space-y-2">
          <Label for="sec-align">Alignement vertical</Label>
          <Combobox
            id="sec-align"
            value={p.align ?? 'start'}
            options={VALIGN_OPTS}
            clearable={false}
            onchange={(v) => update({ align: v })}
          />
        </div>
        <p class="rounded-md bg-amber-50 p-2 text-xs text-amber-700">
          L'ajout de blocs dans les colonnes via l'éditeur arrive dans la prochaine itération. Pour
          l'instant tu peux composer la section depuis le JSON ou utiliser le seed côté backend.
        </p>
      {:else if block.type === 'image'}
        {@const p = block.props as unknown as ImageProps}
        <div class="space-y-2">
          <Label for="img-src">URL de l'image</Label>
          <Input
            id="img-src"
            type="url"
            value={p.src ?? ''}
            oninput={(e) => update({ src: e.currentTarget.value })}
            placeholder="https://…"
          />
        </div>
        <div class="space-y-2">
          <Label for="img-alt">Texte alternatif</Label>
          <Input
            id="img-alt"
            value={p.alt ?? ''}
            oninput={(e) => update({ alt: e.currentTarget.value })}
          />
        </div>
        <div class="space-y-2">
          <Label for="img-fit">Adaptation</Label>
          <Combobox
            id="img-fit"
            value={p.fit ?? 'cover'}
            options={IMG_FIT_OPTS}
            clearable={false}
            onchange={(v) => update({ fit: v })}
          />
        </div>
        <div class="space-y-2">
          <Label for="img-rounded">Arrondi</Label>
          <Combobox
            id="img-rounded"
            value={p.rounded ?? 'md'}
            options={IMG_ROUNDED_OPTS}
            clearable={false}
            onchange={(v) => update({ rounded: v })}
          />
        </div>
        <div class="space-y-2">
          <Label for="img-maxw">Largeur max</Label>
          <Combobox
            id="img-maxw"
            value={p.maxWidth ?? 'lg'}
            options={IMG_MAXW_OPTS}
            clearable={false}
            onchange={(v) => update({ maxWidth: v })}
          />
        </div>
      {:else if block.type === 'spacer'}
        {@const p = block.props as unknown as SpacerProps}
        <div class="space-y-2">
          <Label for="sp-size">Hauteur</Label>
          <Combobox
            id="sp-size"
            value={p.size ?? 'md'}
            options={SPACER_OPTS}
            clearable={false}
            onchange={(v) => update({ size: v })}
          />
        </div>
      {:else if block.type === 'divider'}
        {@const p = block.props as unknown as DividerProps}
        <div class="space-y-2">
          <Label for="dv-variant">Style de ligne</Label>
          <Combobox
            id="dv-variant"
            value={p.variant ?? 'solid'}
            options={DIVIDER_VARIANT_OPTS}
            clearable={false}
            onchange={(v) => update({ variant: v })}
          />
        </div>
        <div class="space-y-2">
          <Label for="dv-color">Couleur</Label>
          <Combobox
            id="dv-color"
            value={p.color ?? 'muted'}
            options={DIVIDER_COLOR_OPTS}
            clearable={false}
            onchange={(v) => update({ color: v })}
          />
        </div>
      {/if}

      <!-- Style panel: shared across every block type that uses outerClasses
           / innerClasses (Hero, FeatureGrid, FAQ, RichText). For others
           (section / spacer / divider / image / cta_button / payment_form)
           the controls still write but the corresponding component just
           ignores them — keeping the UX consistent. -->
      {#if block.type !== 'spacer' && block.type !== 'divider'}
        <div class="space-y-2 border-t pt-4">
          <p class="text-muted-foreground text-xs font-semibold tracking-wide uppercase">Style</p>

          <div class="space-y-1.5">
            <Label for="st-bg" class="text-xs">Arrière-plan</Label>
            <Combobox
              id="st-bg"
              size="sm"
              value={style?.background ?? 'none'}
              options={STYLE_BG_OPTS}
              clearable={false}
              onchange={(v) => updateStyle({ background: v as StyleProps['background'] })}
            />
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div class="space-y-1.5">
              <Label for="st-py" class="text-xs">Padding ↕</Label>
              <Combobox
                id="st-py"
                size="sm"
                value={style?.paddingY ?? 'lg'}
                options={STYLE_PY_OPTS}
                clearable={false}
                onchange={(v) => updateStyle({ paddingY: v as StyleProps['paddingY'] })}
              />
            </div>
            <div class="space-y-1.5">
              <Label for="st-px" class="text-xs">Padding ↔</Label>
              <Combobox
                id="st-px"
                size="sm"
                value={style?.paddingX ?? 'md'}
                options={STYLE_PX_OPTS}
                clearable={false}
                onchange={(v) => updateStyle({ paddingX: v as StyleProps['paddingX'] })}
              />
            </div>
          </div>

          <div class="grid grid-cols-2 gap-2">
            <div class="space-y-1.5">
              <Label for="st-align" class="text-xs">Alignement texte</Label>
              <Combobox
                id="st-align"
                size="sm"
                value={style?.align ?? 'left'}
                options={ALIGN_OPTS}
                clearable={false}
                onchange={(v) => updateStyle({ align: v as StyleProps['align'] })}
              />
            </div>
            <div class="space-y-1.5">
              <Label for="st-mw" class="text-xs">Largeur max</Label>
              <Combobox
                id="st-mw"
                size="sm"
                value={style?.maxWidth ?? 'normal'}
                options={STYLE_MAXW_OPTS}
                clearable={false}
                onchange={(v) => updateStyle({ maxWidth: v as StyleProps['maxWidth'] })}
              />
            </div>
          </div>

          <div class="space-y-1.5">
            <Label for="st-color" class="text-xs">Couleur du texte</Label>
            <Combobox
              id="st-color"
              size="sm"
              value={style?.textColor ?? 'inherit'}
              options={STYLE_TEXT_OPTS}
              clearable={false}
              onchange={(v) => updateStyle({ textColor: v as StyleProps['textColor'] })}
            />
          </div>
        </div>
      {/if}

      <div class="border-t pt-4">
        <Button
          variant="outline"
          class="text-destructive hover:bg-destructive/10 w-full"
          onclick={() => store.removeBlock(block.id)}
        >
          Supprimer ce bloc
        </Button>
      </div>
    </div>
  {/if}
</aside>
