<script lang="ts">
  import { untrack } from 'svelte';
  import { enhance } from '$app/forms';
  import { Eye, EyeOff, Copy, Check, TriangleAlert } from 'lucide-svelte';
  import { Button, Card, Combobox, Input, Label } from '$lib/components/ui';
  import type { ConfigSectionName } from '$lib/api/client';
  import { cn } from '$lib/utils';

  let { data, form } = $props();

  // 'maskable' = valeur non-secrète mais longue (ex. clé publique) : affichée
  // masquée par défaut, révélable via un bouton œil.
  type FieldKind = 'text' | 'number' | 'secret' | 'bool' | 'provider' | 'maskable';
  interface Field {
    name: string;
    label: string;
    kind: FieldKind;
  }
  interface Section {
    key: ConfigSectionName;
    label: string;
    description: string;
    fields: Field[];
    test?: 'smtp' | 'sms';
  }

  const SECTIONS: Section[] = [
    {
      key: 'general',
      label: 'Général',
      description: 'Agrégateur de paiement actif et URL publique du site.',
      fields: [
        { name: 'payment_provider', label: 'Agrégateur de paiement', kind: 'provider' },
        { name: 'site_url', label: 'URL du site', kind: 'text' }
      ]
    },
    {
      key: 'smtp',
      label: 'Email (SMTP)',
      description: 'Serveur d’envoi des emails transactionnels.',
      fields: [
        { name: 'host', label: 'Hôte', kind: 'text' },
        { name: 'port', label: 'Port', kind: 'number' },
        { name: 'user', label: 'Utilisateur', kind: 'text' },
        { name: 'password', label: 'Mot de passe', kind: 'secret' },
        { name: 'from_email', label: 'Expéditeur (From)', kind: 'text' }
      ],
      test: 'smtp'
    },
    {
      key: 'kkiapay',
      label: 'Kkiapay',
      description: 'Identifiants de l’agrégateur Kkiapay.',
      fields: [
        { name: 'public_key', label: 'Clé publique', kind: 'maskable' },
        { name: 'private_key', label: 'Clé privée', kind: 'secret' },
        { name: 'secret_key', label: 'Clé secrète', kind: 'secret' },
        { name: 'sandbox', label: 'Mode sandbox', kind: 'bool' }
      ]
    },
    {
      key: 'cinetpay',
      label: 'CinetPay',
      description: 'Identifiants de l’agrégateur CinetPay.',
      fields: [
        { name: 'site_id', label: 'Site ID', kind: 'text' },
        { name: 'api_key', label: 'Clé API', kind: 'secret' },
        { name: 'sandbox', label: 'Mode sandbox', kind: 'bool' }
      ]
    },
    {
      key: 'sms',
      label: 'SMS',
      description: 'Passerelle SMS générique (URL + clé API).',
      fields: [
        { name: 'provider_url', label: 'URL du provider', kind: 'text' },
        { name: 'api_key', label: 'Clé API', kind: 'secret' },
        { name: 'sender', label: 'Expéditeur (sender ID)', kind: 'text' }
      ],
      test: 'sms'
    }
  ];

  const PROVIDER_OPTS = [
    { value: 'kkiapay', label: 'Kkiapay' },
    { value: 'cinetpay', label: 'CinetPay' }
  ];

  let active = $state<ConfigSectionName>('general');
  const activeSection = $derived(SECTIONS.find((s) => s.key === active)!);

  // Reveal state for maskable/secret fields, keyed by section-field.
  let revealed = $state<Record<string, boolean>>({});
  // Transient "copié" feedback, keyed by section-field.
  let copiedKey = $state<string | null>(null);

  async function copyValue(key: string, value: string) {
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
      copiedKey = key;
      setTimeout(() => {
        if (copiedKey === key) copiedKey = null;
      }, 1500);
    } catch {
      // clipboard unavailable (insecure context) — silently ignore
    }
  }

  // Searchable provider select — local state, seeded once from the loaded
  // value (untrack: we intentionally only want the initial value here).
  let providerValue = $state(
    untrack(() => String(data.settings.general?.values?.payment_provider ?? 'kkiapay'))
  );

  function strVal(section: ConfigSectionName, name: string): string {
    const v = data.settings[section]?.values?.[name];
    return v == null ? '' : String(v);
  }
  function boolVal(section: ConfigSectionName, name: string): boolean {
    return Boolean(data.settings[section]?.values?.[name]);
  }
  function secretSet(section: ConfigSectionName, name: string): boolean {
    return Boolean(data.settings[section]?.secrets?.[name]);
  }
</script>

<div class="mx-auto max-w-5xl space-y-6 p-6">
  <header>
    <h1 class="text-2xl font-semibold tracking-tight">Configuration</h1>
    <p class="text-muted-foreground mt-1 text-sm">
      Paramètres modifiables à chaud — pas de redéploiement. Les secrets sont chiffrés et jamais
      réaffichés.
    </p>
  </header>

  {#if form?.saved}
    <div class="border-primary/30 bg-primary/10 text-primary rounded-md border px-4 py-2 text-sm">
      Section « {form.saved} » enregistrée.
    </div>
  {/if}
  {#if form?.tested}
    <div class="border-primary/30 bg-primary/10 text-primary rounded-md border px-4 py-2 text-sm">
      Test {form.tested} envoyé à {form.to}.
    </div>
  {/if}
  {#if form?.error}
    <div
      class="border-destructive/30 bg-destructive/10 text-destructive rounded-md border px-4 py-2 text-sm"
    >
      {form.error}
    </div>
  {/if}

  <div class="flex flex-col gap-6 md:flex-row">
    <!-- Sidebar -->
    <nav class="shrink-0 md:w-56" aria-label="Sections de configuration">
      <ul class="flex gap-1 overflow-x-auto md:flex-col md:gap-0.5">
        {#each SECTIONS as s (s.key)}
          <li>
            <button
              type="button"
              onclick={() => (active = s.key)}
              aria-current={active === s.key}
              class={cn(
                'w-full rounded-md px-3 py-2 text-left text-sm whitespace-nowrap transition-colors',
                active === s.key
                  ? 'bg-primary/10 text-primary md:border-primary font-medium md:border-l-2'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              )}
            >
              {s.label}
            </button>
          </li>
        {/each}
      </ul>
    </nav>

    <!-- Active section -->
    <div class="min-w-0 flex-1">
      {#key active}
        <Card class="p-6">
          <div class="mb-4">
            <h2 class="text-lg font-medium">{activeSection.label}</h2>
            <p class="text-muted-foreground text-sm">{activeSection.description}</p>
          </div>

          {#if active === 'cinetpay' || (active === 'general' && providerValue === 'cinetpay')}
            <div
              class="mb-4 flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-50 p-3 text-sm text-amber-800"
            >
              <TriangleAlert class="mt-0.5 h-4 w-4 shrink-0" />
              <p>
                <span class="font-medium">CinetPay est en cours d'intégration.</span> Les paiements ne
                sont pas encore confirmés automatiquement — ne l'activez pas comme agrégateur en production.
              </p>
            </div>
          {/if}

          <form method="POST" action="?/save" use:enhance class="space-y-4">
            <input type="hidden" name="section" value={active} />

            {#each activeSection.fields as field (field.name)}
              <div class="space-y-1.5">
                <Label for={`${active}-${field.name}`}>{field.label}</Label>

                {#if field.kind === 'bool'}
                  <div class="flex items-center gap-2">
                    <input
                      id={`${active}-${field.name}`}
                      name={field.name}
                      type="checkbox"
                      checked={boolVal(active, field.name)}
                      class="border-input text-primary focus:ring-ring h-4 w-4 rounded"
                    />
                    <span class="text-muted-foreground text-sm">Activé</span>
                  </div>
                {:else if field.kind === 'provider'}
                  <Combobox
                    id={`${active}-${field.name}`}
                    name={field.name}
                    bind:value={providerValue}
                    options={PROVIDER_OPTS}
                    clearable={false}
                    placeholder="Rechercher un agrégateur…"
                  />
                {:else if field.kind === 'secret'}
                  {@const key = `${active}-${field.name}`}
                  <div class="relative">
                    <Input
                      id={key}
                      name={field.name}
                      type={revealed[key] ? 'text' : 'password'}
                      autocomplete="new-password"
                      class="pr-10"
                      placeholder={secretSet(active, field.name)
                        ? '•••••••• configuré — laisser vide pour conserver'
                        : 'non configuré'}
                    />
                    <button
                      type="button"
                      onclick={() => (revealed[key] = !revealed[key])}
                      aria-label={revealed[key] ? 'Masquer' : 'Afficher la saisie'}
                      aria-pressed={revealed[key] ?? false}
                      class="text-muted-foreground hover:bg-secondary hover:text-foreground focus-visible:ring-ring absolute top-1/2 right-2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md transition-colors focus-visible:ring-2 focus-visible:outline-none"
                    >
                      {#if revealed[key]}
                        <EyeOff class="h-4 w-4" />
                      {:else}
                        <Eye class="h-4 w-4" />
                      {/if}
                    </button>
                  </div>
                {:else if field.kind === 'maskable'}
                  {@const key = `${active}-${field.name}`}
                  {@const val = strVal(active, field.name)}
                  <div class="relative">
                    <Input
                      id={key}
                      name={field.name}
                      type={revealed[key] ? 'text' : 'password'}
                      autocomplete="off"
                      value={val}
                      class="pr-16"
                    />
                    <div
                      class="absolute top-1/2 right-2 flex -translate-y-1/2 items-center gap-0.5"
                    >
                      {#if val}
                        <button
                          type="button"
                          onclick={() => copyValue(key, val)}
                          aria-label="Copier la clé"
                          class={cn(
                            'hover:bg-secondary focus-visible:ring-ring flex h-7 w-7 items-center justify-center rounded-md transition-colors focus-visible:ring-2 focus-visible:outline-none',
                            copiedKey === key
                              ? 'text-emerald-600'
                              : 'text-muted-foreground hover:text-foreground'
                          )}
                        >
                          {#if copiedKey === key}
                            <Check class="h-4 w-4" />
                          {:else}
                            <Copy class="h-4 w-4" />
                          {/if}
                        </button>
                      {/if}
                      <button
                        type="button"
                        onclick={() => (revealed[key] = !revealed[key])}
                        aria-label={revealed[key] ? 'Masquer la clé' : 'Afficher la clé'}
                        aria-pressed={revealed[key] ?? false}
                        class="text-muted-foreground hover:bg-secondary hover:text-foreground focus-visible:ring-ring flex h-7 w-7 items-center justify-center rounded-md transition-colors focus-visible:ring-2 focus-visible:outline-none"
                      >
                        {#if revealed[key]}
                          <EyeOff class="h-4 w-4" />
                        {:else}
                          <Eye class="h-4 w-4" />
                        {/if}
                      </button>
                    </div>
                  </div>
                {:else}
                  <Input
                    id={`${active}-${field.name}`}
                    name={field.name}
                    type={field.kind === 'number' ? 'number' : 'text'}
                    value={strVal(active, field.name)}
                  />
                {/if}
              </div>
            {/each}

            <div class="pt-2">
              <Button type="submit">Enregistrer</Button>
            </div>
          </form>

          {#if activeSection.test === 'smtp'}
            <form method="POST" action="?/testSmtp" use:enhance class="mt-6 border-t pt-4">
              <Label for="smtp-test-to">Tester l’envoi (email)</Label>
              <div class="mt-1.5 flex gap-2">
                <Input
                  id="smtp-test-to"
                  name="to"
                  type="email"
                  placeholder="destinataire@exemple.com"
                />
                <Button type="submit" variant="outline">Envoyer un test</Button>
              </div>
            </form>
          {/if}

          {#if activeSection.test === 'sms'}
            <form method="POST" action="?/testSms" use:enhance class="mt-6 border-t pt-4">
              <Label for="sms-test-to">Tester l’envoi (SMS)</Label>
              <div class="mt-1.5 flex gap-2">
                <Input id="sms-test-to" name="to" type="tel" placeholder="+2250700000000" />
                <Button type="submit" variant="outline">Envoyer un test</Button>
              </div>
            </form>
          {/if}
        </Card>

        <p class="text-muted-foreground mt-3 text-xs">
          Astuce : une valeur laissée vide hérite de la variable d’environnement correspondante.
        </p>
      {/key}
    </div>
  </div>
</div>
