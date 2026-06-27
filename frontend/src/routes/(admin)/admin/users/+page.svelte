<script lang="ts">
  import { enhance } from '$app/forms';
  import {
    Plus,
    Pencil,
    Users as UsersIcon,
    ShieldCheck,
    Shield,
    User as UserIcon,
    Eye,
    Mail,
    Lock,
    EyeOff
  } from 'lucide-svelte';
  import {
    Button,
    Card,
    Combobox,
    Drawer,
    Input,
    Label,
    type ComboboxOption
  } from '$lib/components/ui';

  let { data, form } = $props();

  // Drawer-state local to this page. Opens on "Nouvel utilisateur",
  // closes on success or via the × button / backdrop / Esc.
  let createOpen = $state(false);
  let creating = $state(false);
  let showPassword = $state(false);
  let draftUsername = $state('');
  let draftRole = $state<string>('operator');

  // After a successful create the server returns ``{ created: true }`` via
  // ``form``. Close the drawer and reset the inputs.
  $effect(() => {
    if (form && 'created' in form && form.created) {
      createOpen = false;
      draftUsername = '';
      draftRole = 'operator';
      showPassword = false;
    }
  });

  const formatDate = (iso: string) =>
    new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' }).format(
      new Date(iso)
    );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const roleStyle: Record<string, { icon: any; label: string; color: string }> = {
    super_admin: { icon: ShieldCheck, label: 'Super-admin', color: 'bg-red-100 text-red-700' },
    admin: { icon: Shield, label: 'Admin', color: 'bg-violet-100 text-violet-700' },
    operator: { icon: UserIcon, label: 'Opérateur', color: 'bg-blue-100 text-blue-700' },
    reader: { icon: Eye, label: 'Lecteur', color: 'bg-slate-100 text-slate-700' }
  };

  const ROLE_OPTIONS: ComboboxOption[] = [
    {
      value: 'admin',
      label: 'Admin',
      description: 'Accès complet sauf suppression d’utilisateurs'
    },
    { value: 'operator', label: 'Opérateur', description: 'Lecture, resend, sync paiement' },
    { value: 'reader', label: 'Lecteur', description: 'Lecture seule' }
  ];
</script>

<svelte:head>
  <title>Utilisateurs · CaaS</title>
</svelte:head>

<header class="mb-6 flex items-center justify-between">
  <div>
    <h1 class="text-2xl font-semibold tracking-tight">Utilisateurs</h1>
    <p class="text-muted-foreground mt-1 text-sm">
      Les comptes opérateurs autorisés à se connecter à l'admin.
    </p>
  </div>
  <Button onclick={() => (createOpen = true)}>
    <Plus class="h-4 w-4" /> Nouvel utilisateur
  </Button>
</header>

{#if data.users.length === 0}
  <Card class="flex flex-col items-center justify-center p-12 text-center">
    <UsersIcon class="text-muted-foreground h-10 w-10" />
    <p class="mt-4 font-medium">Aucun utilisateur</p>
    <p class="text-muted-foreground mt-1 text-sm">
      Le super-admin (configuré via les variables d'environnement) n'apparaît jamais ici. Crée des
      opérateurs pour étoffer ton équipe.
    </p>
    <div class="mt-4">
      <Button onclick={() => (createOpen = true)}>
        <Plus class="h-4 w-4" /> Nouvel utilisateur
      </Button>
    </div>
  </Card>
{:else}
  <Card class="overflow-hidden">
    <table class="w-full text-sm">
      <thead class="bg-muted/30 text-muted-foreground border-b text-xs uppercase">
        <tr>
          <th class="px-4 py-2.5 text-left font-medium">Nom d'utilisateur</th>
          <th class="px-4 py-2.5 text-left font-medium">Rôle</th>
          <th class="hidden px-4 py-2.5 text-left font-medium sm:table-cell">Créé le</th>
          <th class="px-4 py-2.5 text-right font-medium">Actions</th>
        </tr>
      </thead>
      <tbody class="divide-y">
        {#each data.users as u (u.id)}
          {@const r = roleStyle[u.role] ?? roleStyle.reader}
          {@const Icon = r.icon}
          <tr class="hover:bg-muted/30">
            <td class="px-4 py-2.5">
              <p class="font-medium">{u.username}</p>
              <p class="text-muted-foreground text-xs sm:hidden">{formatDate(u.created_at)}</p>
            </td>
            <td class="px-4 py-2.5">
              <span
                class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium {r.color}"
              >
                <Icon class="h-3 w-3" />
                {r.label}
              </span>
            </td>
            <td class="text-muted-foreground hidden px-4 py-2.5 sm:table-cell">
              {formatDate(u.created_at)}
            </td>
            <td class="px-4 py-2.5 text-right">
              <a
                href={`/admin/users/${u.id}`}
                class="text-muted-foreground hover:text-foreground inline-flex items-center gap-1 text-sm"
              >
                <Pencil class="h-3.5 w-3.5" /> Éditer
              </a>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </Card>
{/if}

<Drawer
  bind:open={createOpen}
  title="Nouvel utilisateur"
  description="Crée un compte opérateur. Le rôle super_admin reste réservé à l'environnement."
>
  <form
    id="create-user-form"
    method="POST"
    action="?/create"
    use:enhance={() => {
      creating = true;
      return async ({ update }) => {
        await update();
        creating = false;
      };
    }}
    class="space-y-4"
  >
    <div class="space-y-2">
      <Label for="d-username">Email / nom d'utilisateur</Label>
      <div class="relative">
        <Mail
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
        />
        <Input
          id="d-username"
          name="username"
          required
          autocomplete="off"
          bind:value={draftUsername}
          placeholder="prenom.nom@exemple.com"
          class="pl-9"
        />
      </div>
    </div>

    <div class="space-y-2">
      <Label for="d-password">Mot de passe initial</Label>
      <div class="relative">
        <Lock
          class="text-muted-foreground pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2"
        />
        <Input
          id="d-password"
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
      <Label for="d-role">Rôle</Label>
      <Combobox
        id="d-role"
        name="role"
        bind:value={draftRole}
        options={ROLE_OPTIONS}
        clearable={false}
        placeholder="Rechercher un rôle…"
      />
    </div>

    {#if form?.error}
      <p
        class="border-destructive/30 bg-destructive/5 text-destructive rounded-md border p-2 text-sm"
      >
        {form.error}
      </p>
    {/if}
  </form>

  {#snippet footer()}
    <div class="flex items-center justify-end gap-2">
      <Button type="button" variant="outline" onclick={() => (createOpen = false)}>Annuler</Button>
      <Button type="submit" form="create-user-form" disabled={creating}>
        {creating ? 'Création…' : 'Créer le compte'}
      </Button>
    </div>
  {/snippet}
</Drawer>
