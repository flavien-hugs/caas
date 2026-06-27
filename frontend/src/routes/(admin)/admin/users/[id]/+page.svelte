<script lang="ts">
  import { untrack } from 'svelte';
  import { enhance } from '$app/forms';
  import { ArrowLeft, Mail, Lock, Eye, EyeOff, Trash2, Save } from 'lucide-svelte';
  import { Button, Card, Combobox, Input, Label, type ComboboxOption } from '$lib/components/ui';

  const ROLE_OPTIONS: ComboboxOption[] = [
    {
      value: 'admin',
      label: 'Admin',
      description: 'Accès complet sauf suppression d’utilisateurs'
    },
    { value: 'operator', label: 'Opérateur', description: 'Lecture, resend, sync paiement' },
    { value: 'reader', label: 'Lecteur', description: 'Lecture seule' }
  ];

  let { data, form } = $props();

  let submitting = $state(false);
  let deleting = $state(false);
  let showPassword = $state(false);

  // Local form state is seeded from `data.user` once; subsequent server replays
  // come via form.user (after a successful save) and re-sync the inputs.
  let username = $state(untrack(() => data.user.username));
  let role = $state<string>(untrack(() => data.user.role));

  $effect(() => {
    const next = form && 'user' in form ? form.user : null;
    if (next) {
      username = next.username;
      role = next.role;
    }
  });

  const formatDate = (iso: string) =>
    new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(
      new Date(iso)
    );
</script>

<svelte:head>
  <title>{data.user.username} · Utilisateurs</title>
</svelte:head>

<header class="mb-6 flex items-center gap-3">
  <a href="/admin/users" class="text-muted-foreground hover:text-foreground">
    <ArrowLeft class="h-4 w-4" />
  </a>
  <div>
    <h1 class="text-2xl font-semibold tracking-tight">{data.user.username}</h1>
    <p class="text-muted-foreground mt-0.5 text-xs">
      Créé le {formatDate(data.user.created_at)} · Mis à jour le {formatDate(data.user.updated_at)}
    </p>
  </div>
</header>

<Card class="max-w-xl p-6">
  <form
    method="POST"
    action="?/update"
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
      <Label for="username">Email / nom d'utilisateur</Label>
      <div class="relative">
        <Mail
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
        />
        <Input id="username" name="username" required bind:value={username} class="pl-9" />
      </div>
    </div>

    <div class="space-y-2">
      <Label for="password">Nouveau mot de passe</Label>
      <div class="relative">
        <Lock
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
        />
        <Input
          id="password"
          name="password"
          type={showPassword ? 'text' : 'password'}
          autocomplete="new-password"
          placeholder="Laisse vide pour ne pas changer"
          class="pr-10 pl-9"
        />
        <button
          type="button"
          onclick={() => (showPassword = !showPassword)}
          aria-label={showPassword ? 'Masquer le mot de passe' : 'Afficher le mot de passe'}
          class="text-muted-foreground hover:bg-secondary hover:text-foreground absolute top-1/2 right-2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md"
        >
          {#if showPassword}<EyeOff class="h-4 w-4" />{:else}<Eye class="h-4 w-4" />{/if}
        </button>
      </div>
    </div>

    <div class="space-y-2">
      <Label for="role">Rôle</Label>
      <Combobox
        id="role"
        name="role"
        bind:value={role}
        options={ROLE_OPTIONS}
        clearable={false}
        placeholder="Rechercher un rôle…"
      />
    </div>

    {#if form?.error}
      <p class="text-destructive text-sm">{form.error}</p>
    {:else if form && 'saved' in form && form.saved}
      <p class="text-sm text-emerald-600">Modifications enregistrées.</p>
    {/if}

    <div class="flex justify-end gap-2 border-t pt-4">
      <a href="/admin/users">
        <Button type="button" variant="outline">Retour</Button>
      </a>
      <Button type="submit" disabled={submitting}>
        <Save class="h-3.5 w-3.5" />
        {submitting ? 'Enregistrement…' : 'Enregistrer'}
      </Button>
    </div>
  </form>
</Card>

<Card class="border-destructive/30 mt-6 max-w-xl p-6">
  <h2 class="text-destructive text-base font-semibold">Zone dangereuse</h2>
  <p class="text-muted-foreground mt-1 text-sm">
    La suppression d'un utilisateur est définitive. Seul le super-admin peut effectuer cette action.
  </p>
  <form
    method="POST"
    action="?/delete"
    use:enhance={({ cancel }) => {
      if (!confirm(`Supprimer définitivement ${data.user.username} ?`)) {
        cancel();
        return;
      }
      deleting = true;
      return async ({ update }) => {
        await update();
        deleting = false;
      };
    }}
    class="mt-4"
  >
    <Button
      type="submit"
      variant="outline"
      class="text-destructive hover:bg-destructive/10"
      disabled={deleting}
    >
      <Trash2 class="h-3.5 w-3.5" />
      {deleting ? 'Suppression…' : 'Supprimer cet utilisateur'}
    </Button>
  </form>
</Card>
