<script lang="ts">
  import { untrack } from 'svelte';
  import { enhance } from '$app/forms';
  import { Mail, Lock, Eye, EyeOff } from 'lucide-svelte';
  import { Button, Card, Combobox, Input, Label, type ComboboxOption } from '$lib/components/ui';
  import type { ActionData } from './$types';

  const ROLE_OPTIONS: ComboboxOption[] = [
    {
      value: 'admin',
      label: 'Admin',
      description: 'Accès complet sauf suppression d’utilisateurs'
    },
    { value: 'operator', label: 'Opérateur', description: 'Lecture, resend, sync paiement' },
    { value: 'reader', label: 'Lecteur', description: 'Lecture seule' }
  ];

  let { form }: { form: ActionData } = $props();
  let submitting = $state(false);
  let showPassword = $state(false);
  let username = $state(untrack(() => form?.username ?? ''));
  let role = $state(untrack(() => form?.role ?? 'operator'));
</script>

<svelte:head>
  <title>Nouvel utilisateur · CaaS</title>
</svelte:head>

<header class="mb-6">
  <h1 class="text-2xl font-semibold tracking-tight">Nouvel utilisateur</h1>
  <p class="text-muted-foreground mt-1 text-sm">
    Crée un compte opérateur. Le rôle <code>super_admin</code> reste réservé à l'environnement.
  </p>
</header>

<Card class="max-w-xl p-6">
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
      <Label for="username">Email / nom d'utilisateur</Label>
      <div class="relative">
        <Mail
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
        />
        <Input
          id="username"
          name="username"
          required
          autocomplete="off"
          bind:value={username}
          placeholder="prenom.nom@exemple.com"
          class="pl-9"
        />
      </div>
    </div>

    <div class="space-y-2">
      <Label for="password">Mot de passe initial</Label>
      <div class="relative">
        <Lock
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
        />
        <Input
          id="password"
          name="password"
          type={showPassword ? 'text' : 'password'}
          required
          autocomplete="new-password"
          placeholder="8 caractères minimum"
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
      <p class="text-muted-foreground text-xs">
        L'utilisateur pourra le changer après sa première connexion.
      </p>
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
    {/if}

    <div class="flex justify-end gap-2 border-t pt-4">
      <a href="/admin/users">
        <Button type="button" variant="outline">Annuler</Button>
      </a>
      <Button type="submit" disabled={submitting}>
        {submitting ? 'Création…' : 'Créer le compte'}
      </Button>
    </div>
  </form>
</Card>
