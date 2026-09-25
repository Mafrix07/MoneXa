# Système de design MoneXa

## Palette de couleurs

Extraite du fichier `code couleur.jpeg` fourni avec le cahier des charges.

| Couleur | Hex | Usage |
|---|---|---|
| Bleu indigo profond | `#063082` | Primary — confiance fintech |
| Marine foncé | `#1A2539` | Texte, foreground — autorité |
| Crème chaud | `#FFFBF4` | Background — chaleur |
| Or | `#F59E0B` | Accent — CTA, Mobile Money |
| Vert émeraude | `#059669` | Success — validation, paiement OK |
| Rouge | `#DC2626` | Destructive — anomalies, erreur |
| Gris-bleu | `#9DA9C3` | Secondary — muted text |

## Couleurs par canal Mobile Money

| Canal | Couleur | Hex |
|---|---|---|
| T-Money | Indigo profond | `#063082` |
| Moov Money | Vert émeraude | `#059669` |
| Flooz | Or | `#F59E0B` |
| Banque | Gris-bleu | `#9DA9C3` |
| Espèces | Marine light | `#2C3E5A` |

## Typographie

- **Headings** : Plus Jakarta Sans (600/700)
- **Body** : Inter (400/500/600)
- **Mono** : JetBrains Mono (codes, références)

## Composants

### Cards
- Border radius : 16px
- Border : 1px solid `#CBD5E1`
- Padding : 16px (default), 24px (large)

### Boutons
- Primary : background `#F59E0B`, text `#1A2539`
- Elevated : padding `24px 14px`, radius `12px`

### KPI cards
- Icon en haut-gauche dans un carré arrondi avec background `color` alpha 0.1
- Valeur en grand (18px, bold)
- Label en dessous (12px, color muted)

### Audit log entries
- Hash SHA-256 tronqué à 16 caractères + `…`
- Couleur par statut d'action (vert = created, orange = warning, rouge = anomaly)

## Logo

```
+-----------------+
|     /\          |
|    /  \  MoneXa |
|   /----\        |
|  /      \       |
+-----------------+
```

Logo SVG dispo dans `mobile_app/lib/core/theme/app_colors.dart` (couleur) et repris sur le Django Admin.

## Iconographie

- **Lucide** (Flutter : Material Icons)
- Préférence pour les icônes outline, densité moyenne
- Tailles : 20 (inline), 24 (boutons), 44 (touch targets mobile)
