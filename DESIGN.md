# Design System: MoneXa

## 1. Visual Theme & Atmosphere
A ledger-under-shop-light interface: cool mist canvas, deep indigo navy, one gold action. Not a cream artisan boutique and not a neon fintech dashboard. Marketing (Persuade) is asymmetric and airy. Product and mobile (Operate) are denser, familiar, task-first. Variance 6 / Motion 4 / Density 6 on product; landing Density 4.

## 2. Color Palette & Roles
- **Mist Canvas** (#EEF1F6) - page ground
- **Paper Surface** (#F7F8FB) - panels
- **Ink Navy** (#0B1F4D) - display text, sidebar, footer
- **Body Steel** (#4A5A73) - secondary copy
- **Whisper Line** (#D5DCE8) - 1px structure
- **Indigo Core** (#063082) - brand, selection, links
- **Gold Action** (#E08A00) - primary CTA only (saturation kept under 80%)
- **Ledger Green** (#0F6B45) / **Alert Clay** (#B42318) / **Hold Amber** (#B45309) - status only

Dark product theme: charcoal navy surfaces (#0D1320 / #151C2C), same gold CTA.

## 3. Typography Rules
- **Display & UI:** Plus Jakarta Sans (already in the brand). Track-tight headlines, weight-driven hierarchy. No Inter.
- **Numbers:** tabular-nums; IBM Plex Sans on web product tables.
- **Body measure:** ~65ch on marketing prose. Fixed rem scale on product.
- **Banned:** Inter, Fraunces, Instrument Serif, all-caps eyebrows, em-dash as design.

## 4. Component Stylings
- **Buttons:** gold fill / ink text for primary; ghost with line for secondary. 10-12px radius. Active: scale 0.98.
- **Cards:** used only for elevation. Product often uses hairline + paper, not nested cards.
- **Inputs:** label above, 44px min height, gold focus ring.
- **Loaders:** skeleton bars matching KPI/table shape. No center spinner as the only state.
- **Badges:** pill, status color as text + tinted fill. No left accent bars.

## 5. Layout Principles
- Marketing: max 1120px, split hero, never three equal feature towers.
- Product: 248px sidebar, 64px top bar, 1280px content. Mobile: bottom tabs.
- Radius scale: 10px controls, 12px panels, 16px marketing tiles.

## 6. Motion & Interaction
- 180-240ms transform/opacity. Reduced-motion: none.
- Product: state feedback only. Landing: one hero fade-in. No marquees.

## 7. Anti-Patterns (Banned)
No AI purple glow, no cream+brass default, no 3-column icon cards, no fake OS window chrome, no section numbering, no "Scroll to explore", no duplicate Connexion+Commencer with the same intent in one cluster.
