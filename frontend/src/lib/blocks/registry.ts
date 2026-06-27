/**
 * Block registry — single map from BlockType to its UI + schema + defaults.
 *
 * The canvas and inspector look blocks up here rather than knowing about
 * concrete components; that's the only thing that lets us add a new block
 * type without touching the builder.
 */

import {
  LayoutTemplate,
  Grid3x3,
  HelpCircle,
  MousePointerClick,
  AlignLeft,
  CreditCard,
  Columns2,
  Image as ImageIcon,
  Minus,
  MoveVertical
} from 'lucide-svelte';
import type { ZodTypeAny } from 'zod';

import CTAButton from './CTAButton.svelte';
import Divider from './Divider.svelte';
import FAQ from './FAQ.svelte';
import FeatureGrid from './FeatureGrid.svelte';
import Hero from './Hero.svelte';
import ImageBlock from './Image.svelte';
import PaymentForm from './PaymentForm.svelte';
import RichText from './RichText.svelte';
import Section from './Section.svelte';
import Spacer from './Spacer.svelte';
import { BLOCK_SCHEMAS, type BlockType } from './types';

// `any` here is a deliberate escape hatch: lucide-svelte and our block
// components use different Component signatures and unifying them under a
// single Svelte 5 `Component<…>` produces noisy false-positive type errors
// at every render site. The registry only forwards `{ props, mode }` to
// blocks and `{ class }` to icons, which we control directly.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyComponent = any;

export interface BlockDef {
  type: BlockType;
  label: string;
  description: string;
  icon: AnyComponent;
  schema: ZodTypeAny;
  category: 'layout' | 'content' | 'media' | 'interaction';
  /** Defaulted props used when a fresh block is dropped on the canvas. */
  defaults: Record<string, unknown>;
  /** The Svelte component receives ``{ props, mode }``. */
  component: AnyComponent;
}

export const BLOCK_DEFS: Record<BlockType, BlockDef> = {
  section: {
    type: 'section',
    label: 'Section / colonnes',
    description: '1 à 4 colonnes pour disposer plusieurs blocs côte à côte',
    icon: Columns2,
    schema: BLOCK_SCHEMAS.section,
    category: 'layout',
    defaults: {
      columns: 2,
      gap: 'md',
      layout: 'equal',
      align: 'start',
      children: [[], []]
    },
    component: Section
  },
  hero: {
    type: 'hero',
    label: 'Hero',
    description: 'Titre + sous-titre + CTA en pleine largeur',
    icon: LayoutTemplate,
    schema: BLOCK_SCHEMAS.hero,
    category: 'content',
    defaults: {
      headline: 'Un titre accrocheur',
      subheadline: '',
      ctaLabel: '',
      ctaHref: '',
      background: 'light'
    },
    component: Hero
  },
  feature_grid: {
    type: 'feature_grid',
    label: 'Grille de fonctionnalités',
    description: '2–8 cartes en grille',
    icon: Grid3x3,
    schema: BLOCK_SCHEMAS.feature_grid,
    category: 'content',
    defaults: {
      headline: 'Ce que vous obtenez',
      items: [
        { title: 'Fonctionnalité 1', body: 'Description courte.' },
        { title: 'Fonctionnalité 2', body: 'Description courte.' },
        { title: 'Fonctionnalité 3', body: 'Description courte.' }
      ]
    },
    component: FeatureGrid
  },
  faq: {
    type: 'faq',
    label: 'FAQ',
    description: 'Liste pliable de questions / réponses',
    icon: HelpCircle,
    schema: BLOCK_SCHEMAS.faq,
    category: 'content',
    defaults: {
      headline: 'Questions fréquentes',
      items: [
        { question: 'Comment ça marche ?', answer: 'Décrivez le fonctionnement ici.' },
        { question: 'Combien ça coûte ?', answer: 'Décrivez la tarification ici.' }
      ]
    },
    component: FAQ
  },
  rich_text: {
    type: 'rich_text',
    label: 'Texte enrichi',
    description: 'Paragraphes avec Markdown simple',
    icon: AlignLeft,
    schema: BLOCK_SCHEMAS.rich_text,
    category: 'content',
    defaults: {
      markdown:
        'Écrivez votre contenu ici. **Gras** et *italique* sont supportés.\n\nUtilisez une ligne vide pour séparer les paragraphes.'
    },
    component: RichText
  },
  image: {
    type: 'image',
    label: 'Image',
    description: 'Image distante (URL externe) avec coins et taille',
    icon: ImageIcon,
    schema: BLOCK_SCHEMAS.image,
    category: 'media',
    defaults: {
      src: '',
      alt: '',
      fit: 'cover',
      rounded: 'md',
      maxWidth: 'lg'
    },
    component: ImageBlock
  },
  cta_button: {
    type: 'cta_button',
    label: 'Bouton CTA',
    description: 'Un bouton d’action centré',
    icon: MousePointerClick,
    schema: BLOCK_SCHEMAS.cta_button,
    category: 'interaction',
    defaults: {
      label: 'En savoir plus',
      href: 'https://example.com',
      variant: 'default',
      align: 'center'
    },
    component: CTAButton
  },
  payment_form: {
    type: 'payment_form',
    label: 'Formulaire de paiement',
    description: 'Checkout embarqué pour un produit du catalogue',
    icon: CreditCard,
    schema: BLOCK_SCHEMAS.payment_form,
    category: 'interaction',
    defaults: {
      bookId: 'lutte-contre-fraude',
      title: 'Finaliser votre commande',
      ctaLabel: 'Payer maintenant',
      amountHint: '',
      align: 'center',
      width: 'md',
      variant: 'card',
      cardBackground: 'card',
      ctaVariant: 'default'
    },
    component: PaymentForm
  },
  divider: {
    type: 'divider',
    label: 'Séparateur',
    description: 'Une ligne horizontale fine entre deux blocs',
    icon: Minus,
    schema: BLOCK_SCHEMAS.divider,
    category: 'layout',
    defaults: { variant: 'solid', color: 'muted' },
    component: Divider
  },
  spacer: {
    type: 'spacer',
    label: 'Espacement',
    description: 'Bloc vide pour ajuster la respiration verticale',
    icon: MoveVertical,
    schema: BLOCK_SCHEMAS.spacer,
    category: 'layout',
    defaults: { size: 'md' },
    component: Spacer
  }
};

export const BLOCK_TYPES_ORDERED: BlockType[] = [
  'section',
  'hero',
  'feature_grid',
  'rich_text',
  'image',
  'faq',
  'cta_button',
  'payment_form',
  'divider',
  'spacer'
];

export function getBlockDef(type: string): BlockDef | undefined {
  return (BLOCK_DEFS as Record<string, BlockDef>)[type];
}
