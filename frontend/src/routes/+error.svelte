<script lang="ts">
  import { page } from '$app/state';
</script>

<div class="flex min-h-screen items-center justify-center px-6">
  <div class="text-center">
    <p class="text-muted-foreground text-sm font-semibold">{page.status}</p>
    <h1 class="mt-2 text-3xl font-semibold tracking-tight">
      {page.error?.message ?? 'Une erreur est survenue'}
    </h1>
    <a
      href="/"
      class="bg-primary text-primary-foreground mt-6 inline-block rounded-md px-4 py-2 text-sm font-medium hover:opacity-90"
    >
      Retour à l'accueil
    </a>
  </div>
</div>
