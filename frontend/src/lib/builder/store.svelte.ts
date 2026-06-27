/**
 * Reactive page-builder state — Svelte 5 runes ``$state`` only, no Stores API.
 *
 * The store exposes a frozen ``page`` snapshot and a small set of mutators
 * (``addBlock``, ``removeBlock``, ``updateBlockProps``, ``reorder``,
 * ``selectBlock``). ``dirty`` flips ``true`` on every mutation and resets
 * to ``false`` after a successful save via :func:`markClean`.
 *
 * One store per editor page — instantiated in
 * ``routes/(admin)/admin/pages/[id]/+page.svelte``.
 */

import { BLOCK_DEFS } from '$blocks/registry';
import type { Block, BlockType } from '$blocks/types';

export interface PageSnapshot {
  id: string;
  slug: string;
  title: string;
  status: 'draft' | 'published';
  blocks: Block[];
  publishedAt: string | null;
}

function uid(): string {
  // crypto.randomUUID is available in modern browsers + Node 19+; if absent,
  // fall back to a Math.random hash — IDs are only used as React-style keys
  // within the editor, the backend re-checks structure but accepts any id.
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return 'b-' + Math.random().toString(36).slice(2, 10);
}

export function createBuilderStore(initial: PageSnapshot) {
  let title = $state(initial.title);
  let slug = $state(initial.slug);
  let status = $state(initial.status);
  let publishedAt = $state(initial.publishedAt);
  let blocks = $state<Block[]>([...initial.blocks]);
  let selectedBlockId = $state<string | null>(null);
  let dirty = $state(false);

  function _touch() {
    dirty = true;
  }

  return {
    // ----- snapshot accessors (reactive via getters) -------------------------
    get id() {
      return initial.id;
    },
    get title() {
      return title;
    },
    get slug() {
      return slug;
    },
    get status() {
      return status;
    },
    get publishedAt() {
      return publishedAt;
    },
    get blocks() {
      return blocks;
    },
    get selectedBlockId() {
      return selectedBlockId;
    },
    get selectedBlock() {
      return blocks.find((b) => b.id === selectedBlockId) ?? null;
    },
    get dirty() {
      return dirty;
    },

    // ----- mutators ----------------------------------------------------------
    setTitle(next: string) {
      if (next !== title) {
        title = next;
        _touch();
      }
    },

    setSlug(next: string) {
      if (next !== slug) {
        slug = next;
        _touch();
      }
    },

    selectBlock(id: string | null) {
      selectedBlockId = id;
    },

    addBlock(type: BlockType, atIndex?: number) {
      const def = BLOCK_DEFS[type];
      const block: Block = { id: uid(), type, props: { ...def.defaults } };
      const next = [...blocks];
      const idx = atIndex ?? next.length;
      next.splice(idx, 0, block);
      blocks = next;
      selectedBlockId = block.id;
      _touch();
      return block;
    },

    removeBlock(id: string) {
      blocks = blocks.filter((b) => b.id !== id);
      if (selectedBlockId === id) selectedBlockId = null;
      _touch();
    },

    duplicateBlock(id: string) {
      const idx = blocks.findIndex((b) => b.id === id);
      if (idx < 0) return;
      const copy: Block = { ...blocks[idx], id: uid(), props: { ...blocks[idx].props } };
      const next = [...blocks];
      next.splice(idx + 1, 0, copy);
      blocks = next;
      selectedBlockId = copy.id;
      _touch();
    },

    updateBlockProps(id: string, props: Record<string, unknown>) {
      blocks = blocks.map((b) => (b.id === id ? { ...b, props } : b));
      _touch();
    },

    /** Replace the block list (used by drag-drop reorder which mutates atomically). */
    setBlocks(next: Block[]) {
      blocks = next;
      _touch();
    },

    reorder(fromIdx: number, toIdx: number) {
      if (fromIdx === toIdx) return;
      const next = [...blocks];
      const [moved] = next.splice(fromIdx, 1);
      next.splice(toIdx, 0, moved);
      blocks = next;
      _touch();
    },

    /** Called after a successful PATCH /admin/pages/{id}. Replaces in-memory
     *  state with the server's view and resets dirty. */
    syncFromServer(snap: PageSnapshot) {
      title = snap.title;
      slug = snap.slug;
      status = snap.status;
      publishedAt = snap.publishedAt;
      blocks = [...snap.blocks];
      dirty = false;
    },

    markClean() {
      dirty = false;
    }
  };
}

export type BuilderStore = ReturnType<typeof createBuilderStore>;
