# Plateforme SpecGeny - Guide Général (v2.0 - MVP RÉVISÉ)

**🚨 RÉVISION MAJEURE : Simplification Architecture pour MVP 6 Semaines**

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Contexte et Problématique](#contexte-et-problématique)
3. [Solution Proposée](#solution-proposée)
4. [Objectifs Stratégiques](#objectifs-stratégiques)
5. [Architecture et Conception](#architecture-et-conception)
6. [Fonctionnalités MVP](#fonctionnalités-mvp)
7. [Fonctionnalités Futures](#fonctionnalités-futures)
8. [Technologies](#technologies)
9. [Modèle d'Affaires](#modèle-daffaires)
10. [Roadmap](#roadmap)
11. [Métriques de Succès](#métriques-de-succès)
12. [Équipe et Rôles](#équipe-et-rôles)

---

## 🎯 Vue d'Ensemble

**SpecGeny** est une plateforme agentique intelligente qui automatise la génération de documents de spécifications techniques à partir de fichiers projets existants. 

### Vision

Transformer la création de spécifications techniques d'un processus manuel, chronophage et sujet aux erreurs en un workflow assisté par IA, rapide et structuré.

### Proposition de Valeur

- **Gain de temps** : Réduction de 70-80% du temps de rédaction de spécifications
- **Qualité constante** : Spécifications structurées selon des templates standardisés
- **Accessibilité** : Permet aux non-techniques de générer des specs professionnelles
- **Human-in-the-Loop** : Validation humaine à chaque étape critique pour garantir la précision

### Cible Initiale

**MVP Focus : UiPath Process Design Documents (PDD)**

Génération automatique de PDDs pour les projets d'automatisation RPA.

---

## 🔍 Contexte et Problématique

### Problème Identifié

1. **Coût élevé de création manuelle**
   - 5-15 heures pour rédiger une spécification complète
   - Nécessite expertise technique ET rédactionnelle
   - Processus répétitif et peu valorisant

2. **Qualité inconsistante**
   - Manque de standardisation entre équipes
   - Oublis de sections critiques
   - Désalignement entre documentation et implémentation

3. **Barrière à l'entrée**
   - Les équipes non-techniques dépendent d'architectes/leads
   - Goulot d'étranglement dans la phase de conception
   - Documentation obsolète avant même l'implémentation

### Opportunité

L'émergence de LLMs multi-modaux (DeepSeek-Reasoner, Claude Sonnet 4.5) permet d'automatiser l'analyse de fichiers projets (incluant images et diagrammes) et la génération de contenu structuré de qualité professionnelle **en un seul appel API**.

### Inspiration

Le projet s'inspire de [github/spec-kit](https://github.com/github/spec-kit), un toolkit de "Spec-Driven Development" qui structure la création de spécifications en phases distinctes (`/specify`, `/plan`, `/tasks`, `/implement`).

**Notre différenciation** : Automatiser les phases humaines (analyse de contexte, extraction d'intent) via un LLM multimodal unique, simplifiant radicalement l'architecture.

---

## 💡 Solution Proposée

### Workflow Utilisateur (UX)

```
┌─────────────────────────────────────────────────────┐
│  Phase A : Sélection du Template                    │
│  ─────────────────────────────────────────────      │
│  1. Utilisateur sélectionne "UiPath PDD"           │
│  2. Template hardcodé affiché                       │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│  Phase B : Upload de Fichiers Multi-Format          │
│  ─────────────────────────────────────────────      │
│  1. Upload fichiers (txt, md, docx, pdf, png, jpg) │
│  2. Max 10 fichiers, 50 MB total                    │
│  3. Validation côté client                          │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│  Phase C : Génération Intelligente (2-5 min)        │
│  ─────────────────────────────────────────────      │
│  1. Lecture de tous les fichiers (OCR si images)   │
│  2. Un seul appel LLM multimodal avec prompt       │
│  3. Génération structurée Markdown + scores        │
│  4. Sauvegarde job en base (SQLite)                │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│  Phase D : Review & Édition (Human-in-Loop)         │
│  ─────────────────────────────────────────────      │
│  1. Affichage preview avec code couleur            │
│  2. Textareas simples pour édition par section     │
│  3. Possibilité de modifier avant export           │
└─────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────┐
│  Phase E : Export Final                             │
│  ─────────────────────────────────────────────      │
│  1. Téléchargement Markdown (natif)                │
│  2. Export PDF (via Pandoc)                        │
│  3. [Future] Export Word (.docx)                   │
└─────────────────────────────────────────────────────┘
```

### Principe Clé : Simplicité Architecturale

**❌ Ce qu'on NE FAIT PAS (contrairement au document initial) :**
- Multi-agent orchestration avec LangGraph
- Vector database et embeddings (Pinecone)
- Boucle de raffinement itérative
- Système de versioning Git

**✅ Ce qu'on FAIT (MVP pragmatique) :**
- **Un seul appel LLM** multimodal (DeepSeek ou Claude)
- **Context stuffing** : tous les fichiers dans un seul prompt (200K tokens)
- **Génération one-shot** : draft complet en une passe
- **Édition simple** : textareas pour corrections manuelles
- **Storage minimal** : SQLite local + filesystem

**Pourquoi cette simplification ?**
- Les LLMs multimodaux récents (DeepSeek-Reasoner, Claude Vision) traitent texte + images en un seul appel
- Avec 10 fichiers max et 50 MB, la fenêtre de contexte de 200K tokens suffit
- Multi-agents = complexité inutile pour le MVP
- Focus sur la validation de valeur, pas l'architecture parfaite

---

## 🎯 Objectifs Stratégiques

### Court Terme (MVP - 6 semaines)

1. **Validation du concept** : Prouver la faisabilité technique avec UiPath PDDs
2. **Acquisition de 10-20 beta users** (équipes RPA internes/externes)
3. **Temps de génération < 5 minutes** pour un PDD complet
4. **Taux de satisfaction > 80%** sur la qualité du draft

### Moyen Terme (6-12 mois)

1. **Extension à 3-5 types de templates** (PRD, Tech Spec, API Docs)
2. **100+ utilisateurs actifs**
3. **Intégrations** : Jira, Confluence, GitHub, GitLab
4. **Monétisation** : Lancement du modèle consumption-based

### Long Terme (12-24 mois)

1. **Plateforme SaaS multi-tenant**
2. **Marketplace de templates** (communautaire)
3. **Agent autonome** : Génération sans review pour cas simples
4. **Enterprise features** : SSO, on-premise, custom LLMs

---

## 🏗️ Architecture et Conception

### Architecture Simplifiée (MVP)

```
┌──────────────────────────────────────────────────────────┐
│                   Frontend (React + shadcn)               │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │ File Upload│  │ Processing   │  │ Review Editor  │   │
│  │ (Drag-Drop)│  │ Status       │  │ (Textareas)    │   │
│  └────────────┘  └──────────────┘  └────────────────┘   │
└────────────────────────┬─────────────────────────────────┘
                         │ REST API (FastAPI)
┌────────────────────────┴─────────────────────────────────┐
│                      Backend (FastAPI)                    │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Single LLM Pipeline (Simplifié)           │ │
│  │                                                     │ │
│  │  1. File Reader (python-docx, PyPDF2, PIL)         │ │
│  │  2. Context Builder (concaténation + prompt)       │ │
│  │  3. LLM Call (DeepSeek/Claude multimodal)          │ │
│  │  4. Response Parser (Markdown + confidence)        │ │
│  │                                                     │ │
│  └─────────────────────────────────────────────────────┘ │
│  ┌──────────────┐  ┌──────────────┐                      │
│  │SQLite DB     │  │Local Storage │                      │
│  │(jobs, specs) │  │(uploaded files)│                    │
│  └──────────────┘  └──────────────┘                      │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│                  LLM API (External)                       │
│  ┌────────────────┐  OU  ┌────────────────┐             │
│  │ DeepSeek       │      │ Claude Sonnet  │             │
│  │ Reasoner       │      │ 4.5            │             │
│  └────────────────┘      └────────────────┘             │
└──────────────────────────────────────────────────────────┘
```

### Décisions Techniques Clés (Révisées)

| Décision | Choix Initial | Choix Révisé MVP | Justification |
|----------|---------------|------------------|---------------|
| **Architecture backend** | Multi-agents (LangGraph) | Pipeline simple Python | Multi-agents = over-engineering pour MVP |
| **LLM** | Claude Sonnet 4.5 | DeepSeek-Reasoner OU Claude | Benchmark les deux, choisir le meilleur |
| **Stockage fichiers** | AWS S3 / MinIO | Filesystem local | Pas besoin d'object storage pour MVP |
| **Base de données** | PostgreSQL + JSONB | SQLite | Plus simple, pas de setup serveur |
| **Vector DB** | Pinecone | ❌ Aucune | Context stuffing suffit (10 fichiers) |
| **Auth** | Supabase Auth | ❌ Sessions anonymes | localStorage + sessionId suffit |
| **Raffinement** | Boucle itérative | ❌ One-shot uniquement | Complexité inutile pour MVP |
| **Confidence scores** | LLM self-assessment | Heuristiques Python | LLM auto-évaluation = peu fiable |

### Flux de Données Simplifié

```
User Upload → Local Storage (/tmp/uploads)
           → Read All Files (python-docx, PyPDF2, PIL pour images)
           → Build Single Prompt (template + all file contents)
           → LLM API Call (multimodal: text + images)
           → Parse Response (Markdown structuré)
           → Calculate Confidence (heuristiques sur longueur/completeness)
           → Save to SQLite (job_id, session_id, result, timestamp)
           → Return to Frontend → Display + Textareas
           → User Edits → Download (MD ou PDF via Pandoc)
```

### Calcul de Confiance (Heuristiques)

```python
def calculate_section_confidence(section_text: str, source_files: list) -> int:
    """
    Calcule un score de confiance basé sur des heuristiques, 
    pas sur l'auto-évaluation du LLM (peu fiable).
    """
    score = 100
    
    # Déduction si section trop courte
    if len(section_text) < 200:
        score -= 30
    
    # Déduction si phrases génériques détectées
    generic_phrases = [
        "à déterminer", "sera défini", "non spécifié", 
        "to be determined", "will be decided"
    ]
    if any(phrase in section_text.lower() for phrase in generic_phrases):
        score -= 20
    
    # Déduction si aucune référence aux fichiers sources
    has_specific_content = any(
        keyword in section_text.lower() 
        for keyword in extract_keywords_from_files(source_files)
    )
    if not has_specific_content:
        score -= 20
    
    return max(0, score)
```

**Mapping couleurs :**
- 🟢 **Vert** : Score ≥ 80% (haute confiance)
- 🟡 **Jaune** : Score 50-79% (confiance moyenne)
- 🔴 **Rouge** : Score < 50% (faible confiance, à réviser)

---

## 🚀 Fonctionnalités MVP (RÉVISÉ)

### ✅ CORE MVP (4.5 Semaines)

| Feature | Complexité | Temps | Statut | Notes |
|---------|-----------|-------|--------|-------|
| **Multi-format upload** (txt, md, docx, pdf, png, jpg, xlsx) | Faible | 3 jours | ✅ KEEP | LLMs multimodaux rendent les images triviales |
| **Template UiPath PDD** (hardcodé) | Faible | 1 jour | ✅ KEEP | Structure fixe pour MVP |
| **Single LLM call** (DeepSeek/Claude multimodal) | Moyenne | 3 jours | ✅ KEEP | Cœur de la génération |
| **Génération Markdown structuré** | Moyenne | 2 jours | ✅ KEEP | Format de sortie |
| **Confidence heuristiques** (pas LLM) | Faible | 1 jour | ✅ KEEP | Scores fiables basés sur règles |
| **Preview read-only + textareas simples** | Faible | 2 jours | ✅ KEEP | Édition basique par section |
| **Download Markdown** | Faible | 1 jour | ✅ KEEP | Export natif |
| **Export PDF** (via Pandoc) | Faible | 1 jour | ✅ KEEP | Ajout simple, haute valeur |
| **Job persistence** (SQLite) | Faible | 2 jours | ✅ KEEP | Mieux qu'in-memory |
| **Sessions anonymes** (localStorage) | Faible | 1 jour | ✅ KEEP | Pas d'auth pour MVP |
| **Console + file logging** | Faible | 1 jour | ✅ KEEP | Debug essentiel |

**Total : ~18 jours = 3.6 semaines de dev pur**

---

### ⚠️ POLISH PHASE (+1.5 Semaines)

| Feature | Complexité | Temps | Quand l'Ajouter |
|---------|-----------|-------|-----------------|
| **Error handling robuste** | Moyenne | 2 jours | Essentiel pour fiabilité |
| **Loading states & progress** | Faible | 2 jours | UX polish |
| **Validation upload** (taille, format) | Faible | 1 jour | Évite crashs backend |
| **Deploy production** (Vercel + Railway) | Moyenne | 2 jours | Testing en conditions réelles |

**Total : ~7 jours = 1.4 semaines**

---

### ❌ CUT (Hors MVP)

| Feature Coupé | Pourquoi | Quand l'Ajouter |
|---------------|----------|-----------------|
| **Multi-agent orchestration** (LangGraph) | Over-engineering, un LLM suffit | V2.0 si besoin de parallélisme |
| **RAG + Vector DB** (Pinecone) | Context stuffing suffit (10 fichiers) | V2.0 si >50 fichiers par projet |
| **Boucle de raffinement** | Complexité state management | V1.5 après feedback utilisateurs |
| **Versioning Git** | Inutile pour génération one-shot | V1.5 si besoin collaboration |
| **Auth complète** (SSO, SAML) | Sessions anonymes OK pour validation | V1.5 pour monétisation |
| **PostgreSQL + S3** | SQLite + filesystem suffisent | V2.0 pour scale |
| **Monitoring avancé** (Sentry, Datadog) | console.log OK pour <100 users | V1.5 pour production |

---

### Comparaison : Document Initial vs. MVP Révisé

| Fonctionnalité | Document Initial | MVP Révisé | Changement |
|----------------|------------------|------------|------------|
| Architecture backend | Multi-agents (LangGraph) | Single LLM pipeline | ❌ Simplifié |
| Vector DB | Pinecone | Aucune (context stuffing) | ❌ Retiré |
| Storage | PostgreSQL + S3 | SQLite + filesystem | ❌ Simplifié |
| Auth | Supabase Auth | Sessions anonymes | ❌ Retiré |
| Raffinement | 2 itérations + diff | One-shot uniquement | ❌ Retiré |
| Confidence scores | LLM self-assessment | Heuristiques Python | 🔄 Changé |
| Inline editor | WYSIWYG rich text | Textareas simples | 🔄 Simplifié |
| Export PDF | ❌ Future | ✅ MVP | ✅ Ajouté |
| Upload images | Via OCR externe | LLM multimodal natif | 🔄 Simplifié |

**Gain de temps estimé : ~3 semaines** (12 semaines → 6 semaines)

---

## 🔮 Fonctionnalités Futures

### Version 1.1 (Post-MVP)

**F1.1 : Templates Additionnels**
- Product Requirements Document (PRD)
- Technical Design Document (TDD)
- API Documentation

**F1.2 : Customisation de Templates**
- UI pour créer/éditer des templates
- Marketplace communautaire de templates

**F1.3 : Support de Fichiers Avancés**
- `.pptx` avec extraction de diagrammes
- Liens Figma (via API)
- Code source avec AST parsing

### Version 1.5

**F1.5.1 : Collaboration**
- Multi-utilisateurs sur un même spec
- Système de commentaires inline
- Approval workflow

**F1.5.2 : Intégrations**
- Jira : Import d'issues comme input
- Confluence : Export direct en page
- GitHub : Sync avec repository

**F1.5.3 : Raffinement Itératif**
- Boucle de 2-3 itérations avec feedback
- Diff visualisé entre versions
- Régénération ciblée par section

### Version 2.0

**F2.0.1 : Multi-Agent Orchestration**
- Pipeline LangGraph pour projets complexes (50+ fichiers)
- Agents spécialisés (Analyzer, Mapper, Generator)
- Processing parallèle

**F2.0.2 : RAG Avancé**
- Vector database (Pinecone ou Qdrant)
- Embeddings pour recherche sémantique
- Support de >100 fichiers par projet

**F2.0.3 : Enterprise Features**
- SSO (Okta, Azure AD)
- On-premise deployment
- Custom LLM (modèles propriétaires)
- Audit trails complets

**F2.0.4 : Advanced Analytics**
- Benchmarking de qualité de specs
- Suggestions d'amélioration continues
- Prédiction du temps d'implémentation

---

## 🛠️ Technologies

### Stack MVP (Simplifié)

| Couche | Technologie | Justification |
|--------|-------------|---------------|
| **Frontend** | React 18 + TypeScript | Écosystème mature, shadcn/ui |
| **UI Components** | shadcn/ui + Tailwind CSS | Design moderne, accessible |
| **Backend** | FastAPI (Python 3.11+) | Async natif, intégration LLM facile |
| **LLM Provider** | DeepSeek-Reasoner OU Claude Sonnet 4.5 | À benchmarker - meilleur prix/performance |
| **Database** | SQLite | Simple, pas de serveur séparé |
| **File Storage** | Filesystem local (/tmp ou /uploads) | Suffisant pour MVP (<100 users) |
| **Auth** | ❌ Aucune (sessions anonymes localStorage) | Pas nécessaire pour validation |
| **PDF Export** | Pandoc | Conversion MD → PDF en 1 commande |
| **Hosting** | Vercel (Frontend) + Railway (Backend) | Deploy simple, CI/CD intégré |
| **Monitoring** | Console logs + fichiers | Simple, pas de service externe |

### ❌ Technologies RETIRÉES du Stack Initial

| Technologie Retirée | Raison | Quand l'Ajouter |
|---------------------|--------|-----------------|
| LangGraph | Over-engineering pour single LLM call | V2.0 si multi-agents nécessaire |
| Pinecone (Vector DB) | Context stuffing suffit | V2.0 si >50 fichiers par projet |
| PostgreSQL | SQLite suffit pour MVP | V1.5 quand >1000 users |
| AWS S3 / MinIO | Filesystem local OK | V1.5 pour scale |
| Supabase Auth | Sessions anonymes OK | V1.5 pour monétisation |
| Sentry / Posthog | Console logs suffisent | V1.5 pour production |

### Comparaison : Stack Initial vs. Stack MVP

| Composant | Stack Initial | Stack MVP | Économie |
|-----------|---------------|-----------|----------|
| Backend complexity | LangGraph + 5 agents | Simple pipeline Python | -2 semaines dev |
| Database | PostgreSQL + S3 | SQLite + filesystem | -1 semaine setup |
| Vector search | Pinecone ($70/mois) | Aucun (context stuffing) | -$70/mois + -1 semaine |
| Auth | Supabase | localStorage | -4 jours dev |
| Monitoring | Sentry + Posthog | Console logs | -2 jours setup |
| **Total économisé** | - | **~3-4 semaines + $70/mois** | - |

---

## 💰 Modèle d'Affaires

### Stratégie de Monétisation (Post-MVP)

**Modèle Consumption-Based (Pay-as-you-go)**

| Métrique | Prix | Justification |
|----------|------|---------------|
| Génération de spec | 5-10€ / spec | Aligné sur coût API (~2-3€) + marge |
| Stockage | 0.50€ / GB / mois | Coût S3 + buffer |
| ~~Raffinement (iterations)~~ | ~~1€ / itération~~ | ❌ Pas dans MVP |

**Tiers (Future)**

1. **Free Tier**
   - 3 specs / mois
   - Templates standards uniquement
   - Export Markdown seulement

2. **Pro Tier** (29€ / mois)
   - 20 specs / mois
   - Templates custom
   - Tous exports (PDF, Word)
   - Historique 90 jours

3. **Enterprise Tier** (Custom)
   - Specs illimitées
   - SSO / On-premise
   - Support prioritaire
   - SLA 99.9%

### Coûts Estimés (MVP Révisé)

| Poste | Coût Initial | Coût MVP Révisé | Économie |
|-------|-------------|-----------------|----------|
| LLM API (1000 specs @ 3€) | 3 000€ | 3 000€ | - |
| ~~Pinecone (Starter)~~ | ~~70€~~ | ❌ 0€ | **+70€** |
| ~~AWS S3 + RDS~~ | ~~150€~~ | ❌ 0€ (filesystem local) | **+150€** |
| Vercel + Railway | 50€ | 50€ | - |
| ~~Monitoring (Sentry + Posthog)~~ | ~~0€ (free)~~ | ❌ 0€ (console logs) | - |
| **Total mensuel** | **3 270€** | **3 050€** | **-220€/mois** |

**Break-even** : ~380 specs payantes / mois à 8€ pièce (vs. 400 dans version initiale)

---

## 🗓️ Roadmap (RÉVISÉ)

### Phase 0 : Préparation (2 semaines)

- [x] Validation du concept (ce document)
- [ ] Benchmark LLMs (DeepSeek vs Claude)
- [ ] Recherche utilisateurs (interviews 5-10 RPA teams)
- [ ] Setup repository GitHub (monorepo ou séparé)
- [ ] Design UI mockups (Figma) - wireframes simples

### Phase 1 : MVP Core (4.5 semaines)

**Semaine 1-2 : Backend Foundation**
- [ ] Setup FastAPI + SQLite
- [ ] File upload handling (multi-format)
- [ ] File readers (python-docx, PyPDF2, PIL)
- [ ] Template PDD hardcodé (prompt engineering)

**Semaine 3 : LLM Pipeline**
- [ ] Context builder (concaténation fichiers → prompt)
- [ ] LLM integration (DeepSeek ou Claude API)
- [ ] Response parser (Markdown structuré)
- [ ] Confidence calculator (heuristiques)

**Semaine 4 : Frontend Core**
- [ ] React + shadcn setup
- [ ] File upload UI (drag-drop)
- [ ] Processing status (polling)
- [ ] Result preview (syntax-highlighted MD)
- [ ] Textareas pour édition par section

**Semaine 5 (mi-semaine) : Export & Integration**
- [ ] Download Markdown
- [ ] Export PDF (Pandoc integration)
- [ ] End-to-end testing avec vrais fichiers RPA

---

### Phase 2 : Polish & Deploy (1.5 semaines)

**Semaine 5 (fin) - 6 : Production Ready**
- [ ] Error handling robuste (upload fails, timeout, bad generation)
- [ ] Loading states & progress indicators
- [ ] Validation frontend (taille fichiers, formats)
- [ ] Deploy backend (Railway ou Render)
- [ ] Deploy frontend (Vercel)
- [ ] Testing avec 3-5 beta users internes

---

### Phase 3 : Beta Testing (2 semaines) - OPTIONNEL

**Semaine 7-8 : Beta Launch**
- [ ] Onboarding de 10-15 beta users externes
- [ ] Collecte feedback structuré (Google Forms + interviews)
- [ ] Bug fixes prioritaires
- [ ] Optimisation des prompts (based on feedback)

---

### **Timeline Total : 6 Semaines (+ 2 semaines beta optionnelles)**

**Comparaison avec timeline initiale :**
- Document initial : 12 semaines (6 sem MVP + 4 sem beta + 2 sem prod)
- Timeline révisée : **6 semaines** (4.5 sem MVP + 1.5 sem polish)
- **Gain : 6 semaines** grâce à simplification architecture

---

## 📊 Métriques de Succès

### KPIs Techniques

| Métrique | Target MVP | Mesure |
|----------|-----------|--------|
| **Temps de génération** | < 5 min | Median p50 |
| **Uptime** | > 95% | 30-day rolling |
| **Taux de succès génération** | > 90% | Specs complètes / total |
| **Coût API par spec** | < 3€ | Moyenne mensuelle |

### KPIs Produit

| Métrique | Target MVP (6 semaines) | Target 6 mois |
|----------|------------------------|---------------|
| **Beta users actifs** | 10-20 | 100+ |
| **Specs générées / mois** | 50-100 | 500+ |
| **Taux de satisfaction** | > 80% | > 85% |
| **Net Promoter Score (NPS)** | > 40 | > 50 |
| **Temps gagné vs manuel** | > 60% | > 70% |

### KPIs Business (Post-MVP)

| Métrique | Target 6 mois | Target 12 mois |
|----------|---------------|----------------|
| **MRR (Monthly Recurring Revenue)** | 2 000€ | 10 000€ |
| **Paying customers** | 20 | 100 |
| **Customer Acquisition Cost (CAC)** | < 100€ | < 50€ |
| **Lifetime Value (LTV)** | > 300€ | > 600€ |

---

## 👥 Équipe et Rôles

### MVP Team Révisé (Core)

**Tech Lead / Architect** (Vous)
- Architecture simplifiée (pipeline LLM)
- Prompt engineering & optimization
- Décisions techniques & code review

**Backend Engineer** (1 FTE) - OU Tech Lead peut faire seul
- Développement API FastAPI
- Intégration LLM (DeepSeek/Claude)
- SQLite + file handling

**Frontend Engineer** (1 FTE) - OU Tech Lead peut faire seul
- React UI avec shadcn/ui
- Textareas d'édition simples
- Intégration API backend

**UX/UI Designer** (0.5 FTE) - OPTIONNEL
- Wireframes Figma (minimal)
- User testing early beta

**[Optionnel] DevOps** (0.25 FTE)
- Deploy Railway + Vercel
- CI/CD simple (GitHub Actions)

### Compétences Requises (Simplifiées)

- **Backend** : Python, FastAPI, SQLite, python-docx, PyPDF2
- **Frontend** : React, TypeScript, Tailwind CSS, Markdown preview
- **AI/ML** : Prompt engineering, ~~embeddings~~, ~~RAG~~, ~~LangGraph~~
- **DevOps** : Docker, GitHub Actions, Railway/Vercel

**Note :** Un solo dev full-stack peut réaliser ce MVP en 6-7 semaines.

---

## 📚 Ressources et Références

### Inspiration Technique

- [github/spec-kit](https://github.com/github/spec-kit) - Spec-Driven Development toolkit
- ~~[LangGraph](https://langchain-ai.github.io/langgraph/)~~ - ❌ Pas dans MVP
- ~~[LlamaIndex](https://www.llamaindex.ai/)~~ - ❌ Pas dans MVP

### Documentation LLM

- [Anthropic Claude API](https://docs.anthropic.com/)
- [DeepSeek API](https://api-docs.deepseek.com/)

### UI/UX

- [shadcn/ui](https://ui.shadcn.com/) - Component library
- [Radix UI](https://www.radix-ui.com/) - Accessible primitives

### Outils Backend

- [python-docx](https://python-docx.readthedocs.io/) - DOCX parsing
- [PyPDF2](https://pypdf2.readthedocs.io/) - PDF parsing
- [Pandoc](https://pandoc.org/) - Markdown → PDF conversion

---

## 📝 Prochaines Étapes

### Actions Immédiates (Cette Semaine)

1. [x] **Réviser document avec scope réaliste**
2. [ ] **Benchmark LLMs** : DeepSeek-Reasoner vs Claude Sonnet 4.5
   - Test sur 5 fichiers RPA réels
   - Comparer qualité output + coût + latence
3. [ ] **Recruter interviews utilisateurs** (3-5 équipes RPA)
4. [ ] **Setup repository GitHub** (structure simple backend + frontend)
5. [ ] **Créer wireframes Figma** (4-5 écrans max)

### Décisions Techniques à Finaliser

| Décision | Options | Deadline |
|----------|---------|----------|
| **Choix du LLM** | DeepSeek-Reasoner vs Claude Sonnet 4.5 | Fin Semaine 1 |
| **Hosting backend** | Railway vs Render vs Fly.io | Fin Semaine 1 |
| **Structure repo** | Monorepo (Turborepo) vs Repos séparés | Fin Semaine 1 |

---

## 📞 Contact et Suivi

**Project Lead** : [Votre Nom]
**Email** : [votre.email@example.com]
**Slack Channel** : #specgeny-dev
**Notion Board** : [Lien vers board projet]

**Cadence de Review**
- **Daily Standups** : 9h30 (15 min) - si équipe >1 personne
- **Weekly Progress Update** : Vendredi 16h
- **Monthly Stakeholder Demo** : Premier lundi du mois

---

## 📌 Notes de Fin

Ce document est un **living document** qui évoluera au fur et à mesure du développement.

**Version** : 2.0 - MVP Scope Révisé (28 Octobre 2025)
**Dernière mise à jour** : 28 Octobre 2025
**Changements majeurs v2.0** :
- ❌ Retrait multi-agent orchestration (LangGraph)
- ❌ Retrait RAG + vector DB (Pinecone)
- ❌ Retrait PostgreSQL + S3 → SQLite + filesystem
- ✅ Ajout export PDF dans MVP
- ✅ Ajout textareas édition simple
- ⏱️ Timeline réduite : 12 semaines → **6 semaines**

**Prochaine révision** : Après benchmark LLMs (Semaine 1)

---

**SpecGeny** - *Générez des spécifications, pas de la frustration.* 🚀