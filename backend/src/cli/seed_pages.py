"""
Seed builder pages with initial content.

Idempotent: if a page with the seeded slug already exists, the command is
a no-op. To re-seed, delete the page in the admin UI first.

Initial content lives in this file as plain Python dicts — short enough to
be readable, no template engine. Long-term, more elaborate landings should
be built via the admin UI; this command exists to:

1. bootstrap a fresh deployment with the fraude product page that pays the
   bills today (``/p/lutte-contre-fraude``);
2. give the team a smoke-test recipe (``python -m src.cli.seed_pages``
   prints what it created or skipped).
"""

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

import typer

from src.application.ports import PageRepositoryPort
from src.application.use_cases.pages import CreatePage, CreatePageInput, UpdatePage, UpdatePageInput
from src.infrastructure.config.settings import settings
from src.infrastructure.persistence.page_repository import SqlPageRepository
from src.infrastructure.persistence.session import get_session_factory

log = logging.getLogger(__name__)

seed_cli = typer.Typer(pretty_exceptions_show_locals=False, no_args_is_help=True)


# ---- per-product block definitions ------------------------------------------


def _fraude_blocks() -> list[dict]:
    """Hero + Features + FAQ + PaymentForm composing the fraude webinar landing.

    Values pull from settings where possible so a single env var change
    re-prices / re-links without touching the page content.
    """
    price = f"{settings.FRAUDE_WEBINAIRE_PRICE:,} FCFA".replace(",", " ")
    return [
        {
            "id": str(uuid4()),
            "type": "hero",
            "props": {
                "headline": "Lutte contre la fraude en entreprise",
                "subheadline": (
                    "Un webinaire pratique pour détecter, prévenir et réagir face "
                    "aux fraudes internes et externes — outils, processus, retours d'expérience."
                ),
                "ctaLabel": "Réserver ma place",
                "ctaHref": "#payment",
                "background": "gradient",
            },
        },
        {
            "id": str(uuid4()),
            "type": "feature_grid",
            "props": {
                "headline": "Ce que vous repartirez avec",
                "items": [
                    {
                        "title": "Cartographier vos risques",
                        "body": "Identifier les zones où votre entreprise est la plus exposée et prioriser les contrôles.",
                    },
                    {
                        "title": "Mettre en place des contrôles",
                        "body": "Séparation des tâches, double signature, rapprochements bancaires — les bons réflexes.",
                    },
                    {
                        "title": "Réagir face à un incident",
                        "body": "Procédure d'enquête interne, communication, recours juridiques.",
                    },
                    {
                        "title": "Outils & modèles",
                        "body": "Checklists et politiques prêtes à adapter dans votre organisation.",
                    },
                ],
            },
        },
        {
            "id": str(uuid4()),
            "type": "faq",
            "props": {
                "headline": "Questions fréquentes",
                "items": [
                    {
                        "question": "Combien coûte le webinaire ?",
                        "answer": f"{price}, paiement sécurisé Mobile Money ou carte.",
                    },
                    {
                        "question": "Comment je reçois l'accès ?",
                        "answer": (
                            "Dès paiement confirmé, vous recevez le lien du groupe WhatsApp où "
                            "le lien Zoom du webinaire est partagé."
                        ),
                    },
                    {
                        "question": "Le webinaire est-il enregistré ?",
                        "answer": (
                            "Oui — un replay est partagé dans le groupe WhatsApp après la session "
                            "pour les participants inscrits."
                        ),
                    },
                ],
            },
        },
        {
            "id": str(uuid4()),
            "type": "payment_form",
            "props": {
                "bookId": "lutte-contre-fraude",
                "ctaLabel": "Réserver ma place",
                "amountHint": f"Tarif : {price}",
            },
        },
    ]


def _block(type: str, props: dict) -> dict:
    """Helper to build a block dict with a fresh uuid."""
    return {"id": str(uuid4()), "type": type, "props": props}


def _default_landing_blocks() -> list[dict]:
    """A showcase landing page that demonstrates every D1 block:
    sections + columns, style presets (background / padding / align /
    maxWidth), and primitives (Spacer, Divider, Image).

    Authors can duplicate this page to bootstrap a new product landing
    without starting from a blank canvas.
    """
    return [
        # 1. Full-bleed gradient hero
        _block(
            "hero",
            {
                "headline": "Lancez votre prochain produit",
                "subheadline": "Un canevas modulaire pour assembler n'importe quelle landing — sections multi-colonnes, blocs réutilisables, style ajustable au pixel.",  # noqa: E501
                "ctaLabel": "Commencer maintenant",
                "ctaHref": "#cta",
                "background": "gradient",
                "_style": {"paddingY": "xl", "align": "center", "maxWidth": "normal"},
            },
        ),
        # 2. Intro paragraph on muted background
        _block(
            "rich_text",
            {
                "markdown": (
                    "**Concevez librement.** Empilez des sections, glissez des colonnes, "
                    "ajustez le style. Chaque bloc est typé, validé, et restitué tel quel — "
                    "sans aller-retour ni régénération côté serveur."
                ),
                "_style": {
                    "background": "muted",
                    "paddingY": "md",
                    "align": "center",
                    "maxWidth": "narrow",
                },
            },
        ),
        _block("spacer", {"size": "sm"}),
        # 3. Section 2-cols: feature grid + image side-by-side
        _block(
            "section",
            {
                "columns": 2,
                "gap": "lg",
                "layout": "sidebar-right",
                "align": "center",
                "_style": {"paddingY": "lg", "maxWidth": "wide"},
                "children": [
                    [
                        _block(
                            "rich_text",
                            {
                                "markdown": (
                                    "## Construit pour les équipes\n\n"
                                    "Composez vos pages avec des blocs réutilisables. "
                                    "Sections multi-colonnes, espacement préset, "
                                    "couleurs cohérentes — sans code."
                                ),
                                "_style": {"paddingY": "none", "paddingX": "none"},
                            },
                        ),
                        _block(
                            "cta_button",
                            {
                                "label": "Voir la documentation",
                                "href": "https://example.com/docs",
                                "variant": "outline",
                                "align": "left",
                            },
                        ),
                    ],
                    [
                        _block(
                            "image",
                            {
                                "src": "https://images.unsplash.com/photo-1551434678-e076c223a692?auto=format&fit=crop&w=900&q=80",  # noqa: E501
                                "alt": "Équipe en train de collaborer autour d'un écran",
                                "fit": "cover",
                                "rounded": "lg",
                                "maxWidth": "full",
                            },
                        ),
                    ],
                ],
            },
        ),
        # 4. Feature grid on muted bg
        _block(
            "feature_grid",
            {
                "headline": "Tout ce qu'il faut pour shipper",
                "items": [
                    {"title": "Sections & colonnes", "body": "1 à 4 colonnes avec dispositions sidebar prêtes à l'emploi."},
                    {"title": "Style sans CSS", "body": "Présets background / padding / align / largeur max."},
                    {"title": "Blocs typés", "body": "Validation Zod côté client, output déterministe côté rendu."},
                ],
                "_style": {"background": "muted", "paddingY": "lg"},
            },
        ),
        _block("divider", {"variant": "solid", "color": "muted"}),
        # 5. Section 3-cols of testimonials/values
        _block(
            "section",
            {
                "columns": 3,
                "gap": "md",
                "align": "stretch",
                "_style": {"paddingY": "lg", "paddingX": "md", "maxWidth": "wide"},
                "children": [
                    [
                        _block(
                            "rich_text",
                            {
                                "markdown": (
                                    "### Rapide\n\nSection / colonnes / style sans manipuler de code, ni régénérer le bundle."
                                ),
                                "_style": {"paddingY": "none", "paddingX": "none", "align": "center"},
                            },
                        ),
                    ],
                    [
                        _block(
                            "rich_text",
                            {
                                "markdown": (
                                    "### Cohérent\n\nLes presets s'appuient sur le design system — une seule source de vérité visuelle."  # noqa: E501
                                ),
                                "_style": {"paddingY": "none", "paddingX": "none", "align": "center"},
                            },
                        ),
                    ],
                    [
                        _block(
                            "rich_text",
                            {
                                "markdown": (
                                    "### Évolutif\n\nAjouter un nouveau type de bloc = un fichier `.svelte` + un schéma Zod. Pas de déploiement backend."  # noqa: E501
                                ),
                                "_style": {"paddingY": "none", "paddingX": "none", "align": "center"},
                            },
                        ),
                    ],
                ],
            },
        ),
        # 6. FAQ
        _block(
            "faq",
            {
                "headline": "Questions fréquentes",
                "items": [
                    {
                        "question": "Comment composer une page ?",
                        "answer": "Glissez des blocs depuis la bibliothèque de gauche, cliquez pour les sélectionner, ajustez les contrôles à droite.",  # noqa: E501
                    },
                    {
                        "question": "Puis-je dupliquer cette page ?",
                        "answer": "Utilisez la commande `seed-pages` du CLI backend, ou copiez le JSON des blocs depuis l'API.",
                    },
                    {
                        "question": "Comment ajouter un nouveau type de bloc ?",
                        "answer": "Ajoutez un schéma Zod, un composant Svelte qui accepte `{ props, mode }`, et une entrée dans le registre. Aucun changement backend nécessaire.",  # noqa: E501
                    },
                ],
            },
        ),
        _block("spacer", {"size": "md"}),
        # 7. Final CTA section, dark background
        _block(
            "section",
            {
                "columns": 1,
                "_style": {
                    "background": "dark",
                    "paddingY": "xl",
                    "paddingX": "md",
                    "maxWidth": "normal",
                    "align": "center",
                },
                "children": [
                    [
                        _block(
                            "rich_text",
                            {
                                "markdown": (
                                    "## Prêt à concevoir votre prochaine page ?\n\n"
                                    "Dupliquez ce modèle, gardez ce qui fonctionne, remplacez le reste."
                                ),
                                "_style": {
                                    "paddingY": "none",
                                    "paddingX": "none",
                                    "textColor": "white",
                                    "align": "center",
                                },
                            },
                        ),
                        _block(
                            "cta_button",
                            {
                                "label": "Créer ma page",
                                "href": "/admin/pages/new",
                                "variant": "default",
                                "align": "center",
                            },
                        ),
                    ]
                ],
            },
        ),
    ]


SEEDS: dict[str, dict] = {
    "lutte-contre-fraude": {
        "title": "Lutte contre la fraude en entreprise",
        "blocks": _fraude_blocks,
        "publish": True,
    },
    "modele-landing": {
        "title": "Modèle — landing modulaire",
        "blocks": _default_landing_blocks,
        # Kept as DRAFT so it's not publicly indexed at /p/modele-landing;
        # authors discover it through the admin UI and duplicate from there.
        "publish": False,
    },
}


async def _seed(repo: PageRepositoryPort) -> None:
    create = CreatePage(pages=repo)
    update = UpdatePage(pages=repo)

    for slug, spec in SEEDS.items():
        existing = await repo.get_by_slug(slug)
        if existing is not None:
            typer.echo(f"= {slug} (already exists, status={existing.status.value})")
            continue

        page = await create.execute(CreatePageInput(slug=slug, title=spec["title"]))
        blocks_data: list[dict] = spec["blocks"]() if callable(spec["blocks"]) else spec["blocks"]
        await update.execute(UpdatePageInput(page_id=page.id, blocks=blocks_data))
        if spec.get("publish"):
            published = await repo.get(page.id)
            assert published is not None
            await repo.save(published.publish())
            typer.echo(f"+ {slug} (created and published)")
        else:
            typer.echo(f"+ {slug} (created as draft)")


def _build_repo() -> SqlPageRepository:
    return SqlPageRepository(session_factory=get_session_factory())


@seed_cli.command("pages")
def seed_pages_cmd() -> None:
    """Idempotent seed for builder pages (fraude product today)."""
    asyncio.run(_seed(_build_repo()))


# Helper exported for the main CLI's wrapper command.
def run_seed_pages() -> None:
    asyncio.run(_seed(_build_repo()))


if __name__ == "__main__":
    seed_cli()
