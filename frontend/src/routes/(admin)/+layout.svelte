<script lang="ts">
  import { page } from '$app/state';
  import { enhance } from '$app/forms';
  import {
    LayoutDashboard,
    FileText,
    Receipt,
    Users,
    SlidersHorizontal,
    LogOut,
    PanelLeftClose,
    PanelLeftOpen
  } from 'lucide-svelte';
  import { can, Permission, type Role } from '$lib/permissions';
  import { cn } from '$lib/utils';

  let { data, children } = $props();

  interface NavItem {
    href: string;
    label: string;
    icon: typeof LayoutDashboard;
    permission?: Permission;
  }

  interface NavGroup {
    label: string;
    items: NavItem[];
  }

  // UI-only gating; the backend re-enforces every permission via
  // `require_permission`. Hiding the link just keeps users out of dead-ends.
  const NAV: NavGroup[] = [
    {
      label: 'Pilotage',
      items: [
        {
          href: '/admin',
          label: 'Tableau de bord',
          icon: LayoutDashboard,
          permission: Permission.READ_STATS
        },
        {
          href: '/admin/transactions',
          label: 'Transactions',
          icon: Receipt,
          permission: Permission.READ_TRANSACTIONS
        }
      ]
    },
    {
      label: 'Contenu',
      items: [
        {
          href: '/admin/pages',
          label: 'Pages',
          icon: FileText,
          permission: Permission.MANAGE_PAGES
        }
      ]
    },
    {
      label: 'Équipe',
      items: [
        {
          href: '/admin/users',
          label: 'Utilisateurs',
          icon: Users,
          permission: Permission.LIST_USERS
        }
      ]
    },
    {
      label: 'Système',
      items: [
        {
          href: '/admin/settings',
          label: 'Configuration',
          icon: SlidersHorizontal,
          permission: Permission.MANAGE_SETTINGS
        }
      ]
    }
  ];

  /** Filter each group's items by the current role, then drop groups that
   *  became empty (e.g. an operator who has no permission to manage users
   *  shouldn't see an "Équipe" header with nothing under it). */
  const visibleGroups = $derived(
    NAV.map((group) => ({
      ...group,
      items: group.items.filter(
        (item) => !item.permission || can(data.user?.role as Role, item.permission)
      )
    })).filter((g) => g.items.length > 0)
  );

  // Collapse state — persisted to localStorage so the choice carries
  // across reloads and route changes. Defaults to expanded on first visit.
  const STORAGE_KEY = 'caas:sidebar-collapsed';
  let collapsed = $state(false);

  $effect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === 'true') collapsed = true;
  });

  $effect(() => {
    localStorage.setItem(STORAGE_KEY, String(collapsed));
  });
</script>

<div class="flex min-h-screen">
  <aside
    class={cn(
      'bg-muted/30 hidden shrink-0 border-r transition-[width] duration-150 md:flex md:flex-col',
      collapsed ? 'w-14 px-1.5 py-3' : 'w-60 px-3 py-4'
    )}
  >
    <div class={cn('flex items-center', collapsed ? 'justify-center' : 'justify-between gap-2')}>
      {#if !collapsed}
        <a href="/admin" class="truncate px-1 text-base font-semibold tracking-tight">CaaS Admin</a>
      {/if}
      <button
        type="button"
        onclick={() => (collapsed = !collapsed)}
        aria-label={collapsed ? 'Déplier la barre latérale' : 'Replier la barre latérale'}
        title={collapsed ? 'Déplier' : 'Replier'}
        class="text-muted-foreground hover:bg-secondary hover:text-foreground flex h-8 w-8 shrink-0 items-center justify-center rounded-md"
      >
        {#if collapsed}
          <PanelLeftOpen class="h-4 w-4" />
        {:else}
          <PanelLeftClose class="h-4 w-4" />
        {/if}
      </button>
    </div>

    <nav class={cn('mt-4 flex-1', collapsed ? 'space-y-3' : 'space-y-4')}>
      {#each visibleGroups as group, gi (group.label)}
        <div class="space-y-1">
          {#if !collapsed}
            <p
              class="text-muted-foreground/70 px-2 text-[10px] font-semibold tracking-wide uppercase"
            >
              {group.label}
            </p>
          {:else if gi > 0}
            <div class="bg-muted-foreground/15 mx-auto h-px w-6" role="separator"></div>
          {/if}
          {#each group.items as item (item.href)}
            {@const Icon = item.icon}
            {@const active =
              page.url.pathname === item.href || page.url.pathname.startsWith(item.href + '/')}
            <a
              href={item.href}
              title={collapsed ? item.label : undefined}
              class={cn(
                'flex items-center rounded-md text-sm transition-colors',
                collapsed ? 'h-9 w-full justify-center' : 'gap-2 px-2 py-2',
                active
                  ? 'bg-secondary text-secondary-foreground font-medium'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
              )}
            >
              <Icon class="h-4 w-4 shrink-0" />
              {#if !collapsed}
                <span class="truncate">{item.label}</span>
              {/if}
            </a>
          {/each}
        </div>
      {/each}
    </nav>

    <div class={cn('mt-4 border-t', collapsed ? 'pt-3' : 'pt-3')}>
      {#if !collapsed}
        <p class="text-muted-foreground px-2 text-xs">Connecté en tant que</p>
        <p class="truncate px-2 text-sm font-medium">{data.user?.username}</p>
        <p class="text-muted-foreground px-2 text-xs">{data.user?.role}</p>
      {/if}

      <form
        method="POST"
        action="/logout"
        use:enhance
        class={cn('mt-2', collapsed ? '' : 'px-2')}
      >
        <button
          type="submit"
          title={collapsed ? `Se déconnecter (${data.user?.username})` : undefined}
          class={cn(
            'text-muted-foreground hover:bg-secondary hover:text-foreground flex items-center rounded-md text-sm',
            collapsed ? 'h-9 w-full justify-center' : 'w-full gap-2 px-1.5 py-2'
          )}
        >
          <LogOut class="h-4 w-4 shrink-0" />
          {#if !collapsed}
            <span>Se déconnecter</span>
          {/if}
        </button>
      </form>
    </div>
  </aside>

  <main class="flex-1 overflow-x-hidden">
    <div class="px-6 py-5">
      {@render children()}
    </div>
  </main>
</div>
