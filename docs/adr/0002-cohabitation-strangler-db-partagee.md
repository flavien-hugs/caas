# ADR-0002 — Cohabitation strangler avec le legacy sur DB partagée

- **Statut** : Accepté
- **Date** : 2026-06-16

## Contexte

Une application legacy (`app/`) sert déjà des paiements en production sur une
base Postgres existante. Réécrire d'un bloc serait risqué. On veut migrer
progressivement (pattern *strangler fig*) sans interruption ni double base.

## Décision

Le nouveau backend **cohabite** avec le legacy sur la **même base Postgres** et
les **mêmes tables** (notamment `transactions`). En conséquence :

- Les `SQLModel` (`infrastructure/persistence/models.py`) mappent le schéma
  existant **à l'identique**.
- Toute évolution de schéma est **additive uniquement** (nouvelles colonnes
  nullables), introduite via les migrations Alembic du nouveau backend.
- La chaîne Alembic est **verrouillée en CI** (`test_alembic_migrations.py` :
  upgrade head + round-trip insert).
- Le profil compose `migrate` est **opt-in** (ne tourne pas par défaut) ; sur
  une base déjà à jour héritée, on peut `alembic stamp head`.

## Conséquences

**Positives**
- Migration sans big-bang ; le legacy et le nouveau lisent/écrivent les mêmes
  transactions.
- Pas de synchronisation de données entre deux bases.

**Négatives / suivi**
- Contrainte forte : **interdit** de supprimer/renommer des colonnes tant que la
  cohabitation dure (autogenerate ne doit jamais proposer de DROP).
- Le `provider` n'est pas persisté par ligne en Phase 1 (réglage déploiement) ;
  passera en colonne quand le legacy sera retiré.
- Fin de vie : un ADR ultérieur actera le retrait du legacy et la reprise pleine
  du schéma.
