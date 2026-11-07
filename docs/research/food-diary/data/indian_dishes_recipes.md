# Indian dishes as documented recipes (slice 3 data prep)

Status: **PENDING DIETITIAN REVIEW**. No nutrient totals are given on purpose; the app calculates them from the ingredient rows.

## How to read this file

- Ingredient ids are `fdc_id` values from `usda_ingredients.csv` (USDA FoodData Central SR Legacy, CC0). Ingredient grams are for the **raw** (or stated) form.
- **Source status:** I did not find a published recipe book with gram quantities that I could verify in this session. Every recipe below is therefore marked `[assumed — needs dietitian]`: typical home-cooking proportions, not a cited standard recipe. The only published anchors used are the NIN serving definitions (ICMR-NIN *Dietary Guidelines for Indians 2024*, Annexures I and II, and *Dietary Guidelines for Indians, A Manual*, NIN 2011, Annexure 8 for the dish names and serving sizes: 1 phulka, 1 cup rice, 2 idli, 1 dosa, 1 cup dal and so on). Annexure 8 gives energy per serving, not grams, so it is a dish-list reference only.
- **Cooked yield** is an assumption in every recipe. The app should let the user weigh their own batch; a dietitian should weigh test batches before these are published.
- **Serving units** use `household_units.csv` keys. Where a unit has no grams there (piece-type dishes), the serving is given as a count and the per-piece grams are **empty until weighed** (never invented).
- **Data gaps (no FDC SR Legacy row):** paneer, flattened rice (poha), jaggery, curry leaves, hing, garam masala, green chilli, ghee-free "vanaspati", buffalo milk, idli/dosa batter. Recipes that need them say so and list the item as `GAP`.
- Chilli powder proxy: `170932` (cayenne or red pepper) is a stand-in, flagged `[proxy]`. Oil: `171017` (sunflower) is used as a generic cooking oil; swap for the user's oil.

---

## 1. Roti / chapati (plain) `[assumed — needs dietitian]`
- Ingredients: atta `168893` 40 g, water (no nutrients) as needed.
- Cooked yield: 1 roti, about 1 piece; weigh to set grams (`roti_homemade_medium` is empty). Packaged fallbacks: 43 g (whole wheat, `174075`).
- Servings: 1 roti = 1 piece (NIN lists "1 phulka" as a serving).

## 2. Plain rice, boiled `[assumed — needs dietitian]`
- Ingredients: rice, white raw `169756` 100 g, water.
- Cooked yield: about 250 g (assumption; USDA lists cooked white rice `168878` as a separate row, which is the better entry when the user logs cooked rice).
- Servings: 1 katori_nin_m (200 ml) cooked, grams from density row `density_168878` (derived, 0.668 g/ml); NIN Annexure 8 serves "1 cup".

## 3. Dal tadka (toor) `[assumed — needs dietitian]`
- Ingredients: toor dal `172436` 50 g; onion `170000` 30 g; tomato `170457` 40 g; garlic `169230` 5 g; sunflower oil `171017` 8 g; cumin `170923` 1 g; turmeric `172231` 1 g; chilli powder `170932` [proxy] 1 g; salt `173468` 2 g; water.
- Cooked yield: about 350 g.
- Servings: 1 katori_nin_s (155 ml) or 1 katori_nin_m (200 ml); NIN Annexure 8: "plain dhal, half cup". Grams from density only if the dietitian confirms dal-with-water density.

## 4. Moong dal (yellow, plain) `[assumed — needs dietitian]`
- Ingredients: moong `174256` 50 g; turmeric `172231` 1 g; salt `173468` 2 g; oil `171017` 5 g; cumin `170923` 1 g; water.
- Cooked yield: about 300 g. Servings: 1 katori_nin_m.

## 5. Rajma masala `[assumed — needs dietitian]`
- Ingredients: rajma `173744` 60 g (raw weight); onion `170000` 60 g; tomato `170457` 80 g; garlic `169230` 6 g; ginger `169231` 6 g; oil `171017` 10 g; cumin `170923` 1 g; coriander seed `170922` 2 g; turmeric `172231` 1 g; chilli powder `170932` [proxy] 1 g; salt `173468` 3 g; water.
- Cooked yield: about 400 g. Servings: 1 katori_nin_m.

## 6. Chole (chickpea curry) `[assumed — needs dietitian]`
- Ingredients: chana `173756` 60 g (raw weight); onion `170000` 60 g; tomato `170457` 80 g; garlic `169230` 6 g; ginger `169231` 6 g; oil `171017` 10 g; cumin `170923` 1 g; coriander seed `170922` 2 g; turmeric `172231` 1 g; chilli powder `170932` [proxy] 1 g; salt `173468` 3 g; water.
- Cooked yield: about 400 g. Servings: 1 katori_nin_m.

## 7. Poha `[assumed — needs dietitian]` `GAP: flattened rice`
- Ingredients: **poha (flattened rice) 60 g dry: no FDC SR Legacy row, so do not substitute raw rice**; onion `170000` 40 g; potato `170026` 30 g; peanuts `172430` 10 g; oil `171017` 8 g; turmeric `172231` 0.5 g; lemon juice `167747` 5 g; salt `173468` 2 g.
- Cooked yield: about 220 g. Servings: 1 cup (NIN Annexure 8 lists "1 cup poha"); cup volume as katori_nin_m, grams from weighed batch.
- Blocked until a poha row exists (IFCT after NIN permission, or a dietitian-sourced entry).

## 8. Upma (rava) `[assumed — needs dietitian]`
- Ingredients: semolina `168933` 50 g; onion `170000` 30 g; carrot `170393` 20 g; peas `170419` 15 g; oil `171017` 8 g; mustard seed `170929` 1 g; salt `173468` 2 g; water.
- Cooked yield: about 250 g. Servings: 1 cup (NIN Annexure 8: "1 cup upma").

## 9. Idli `[assumed — needs dietitian]` `GAP: idli batter`
- Ingredients (batter, raw, before steaming): rice white raw `169756` 100 g; urad (mungo) `174259` 33 g; salt `173468` 2 g; water. Typical rice:urad ratio is about 3:1 by weight in home recipes (assumption).
- Cooked yield: about 8 idli; grams per idli **empty until weighed** (`idli` row has no source).
- Servings: 2 idli (NIN Annexure 8 serving). Because batter water changes yield, log by weighed idli grams.

## 10. Dosa, plain `[assumed — needs dietitian]`
- Ingredients: rice white raw `169756` 100 g; urad `174259` 33 g; oil `171017` 5 g (for the pan); salt `173468` 2 g; water.
- Cooked yield: about 6 dosas; grams per dosa **empty until weighed** (`dosa_plain`). Servings: 1 dosa (NIN Annexure 8).

## 11. Sambar `[assumed — needs dietitian]` `GAP: sambar powder, drumstick pod`
- Ingredients: toor dal `172436` 40 g; onion `170000` 40 g; tomato `170457` 50 g; carrot `170393` 30 g; brinjal `169228` 30 g; tamarind `167763` 5 g; oil `171017` 5 g; mustard seed `170929` 1 g; fenugreek seed `171324` 0.5 g; turmeric `172231` 1 g; coriander seed `170922` 2 g; chilli powder `170932` [proxy] 1 g; salt `173468` 3 g; water.
- Cooked yield: about 600 g. Servings: 1 cup (NIN Annexure 8: "1 cup sambar").

## 12. Paneer bhurji `[assumed — needs dietitian]` `GAP: paneer`
- Ingredients: **paneer 100 g: no FDC SR Legacy row; do not substitute cottage cheese**; onion `170000` 40 g; tomato `170457` 50 g; oil `171017` 8 g; cumin `170923` 1 g; turmeric `172231` 0.5 g; salt `173468` 1.5 g.
- Cooked yield: about 180 g. Servings: 1 katori_nin_s. Blocked until a paneer row exists (IFCT or a dietitian-sourced label value).

## 13. Egg bhurji `[assumed — needs dietitian]`
- Ingredients: egg `171287` 100 g (2 large, 50 g each); onion `170000` 30 g; tomato `170457` 30 g; oil `171017` 6 g; turmeric `172231` 0.5 g; salt `173468` 1 g.
- Cooked yield: about 150 g. Servings: 1 serving = whole batch (2 eggs).

## 14. Khichdi `[assumed — needs dietitian]`
- Ingredients: rice white raw `169756` 50 g; moong `174256` 25 g; oil `171017` 5 g (or ghee `173412` 5 g); cumin `170923` 1 g; turmeric `172231` 0.5 g; salt `173468` 2 g; water.
- Cooked yield: about 400 g. Servings: 1 cup (NIN Annexure 8: "1 cup kichidi"); 1 katori_nin_m.

## 15. Curd rice `[assumed — needs dietitian]`
- Ingredients: rice cooked `168878` 150 g; curd `171284` 120 g; milk `171265` 30 g; salt `173468` 1 g; mustard seed `170929` 0.5 g; oil `171017` 3 g.
- Cooked yield: about 300 g. Servings: 1 katori_nin_m.

## 16. Aloo sabzi (dry) `[assumed — needs dietitian]`
- Ingredients: potato raw `170026` 200 g; onion `170000` 40 g; oil `171017` 10 g; cumin `170923` 1 g; turmeric `172231` 0.5 g; chilli powder `170932` [proxy] 0.5 g; salt `173468` 2 g.
- Cooked yield: about 220 g (assumption; oil absorption and water loss vary). Servings: 1 cup (NIN Annexure 8: "vegetable, dry, 1 cup").

## 17. Aloo gobi `[assumed — needs dietitian]`
- Ingredients: cauliflower `169986` 150 g; potato raw `170026` 100 g; onion `170000` 40 g; tomato `170457` 40 g; oil `171017` 10 g; cumin `170923` 1 g; turmeric `172231` 0.5 g; coriander seed `170922` 1 g; salt `173468` 2 g.
- Cooked yield: about 280 g. Servings: 1 cup (NIN Annexure 8, dry vegetable).

## 18. Bhindi (okra) sabzi `[assumed — needs dietitian]`
- Ingredients: okra `169260` 200 g; onion `170000` 40 g; oil `171017` 10 g; cumin `170923` 1 g; turmeric `172231` 0.5 g; salt `173468` 2 g.
- Cooked yield: about 170 g. Servings: 1 cup (dry vegetable).

## 19. Baingan bharta `[assumed — needs dietitian]`
- Ingredients: brinjal `169228` 250 g; onion `170000` 50 g; tomato `170457` 60 g; garlic `169230` 5 g; oil `171017` 10 g; cumin `170923` 1 g; turmeric `172231` 0.5 g; salt `173468` 2 g.
- Cooked yield: about 250 g. Servings: 1 katori_nin_m.

## 20. Palak dal `[assumed — needs dietitian]`
- Ingredients: masoor `172420` 40 g; spinach `168462` 80 g; onion `170000` 30 g; garlic `169230` 4 g; oil `171017` 6 g; cumin `170923` 1 g; turmeric `172231` 0.5 g; salt `173468` 2 g; water.
- Cooked yield: about 350 g. Servings: 1 katori_nin_m.

## 21. Chicken curry `[assumed — needs dietitian]`
- Ingredients: chicken `171052` 200 g (raw, meat only: boneless weight; if the user weighs bone-in, convert first); onion `170000` 80 g; tomato `170457` 80 g; garlic `169230` 8 g; ginger `169231` 8 g; oil `171017` 15 g; coriander seed `170922` 2 g; cumin `170923` 1 g; turmeric `172231` 1 g; chilli powder `170932` [proxy] 1 g; salt `173468` 3 g; water.
- Cooked yield: about 400 g. Servings: 1 katori_nin_s (NIN Annexure 8 serves "3/4 cup chicken curry").

## 22. Tea with milk and sugar (chai) `[assumed — needs dietitian]`
- Ingredients: milk `171265` 100 g; brewed tea `173227` 100 g (as the tea decoction); sugar `169655` 5 g (1 tsp; adjust).
- Cooked yield: about 200 g. Servings: 1 cup as a small cup (about 150 ml); grams from the weighed or recipe total. FDC has no loose-tea-leaf row, so the brewed-tea row stands in for the decoction.

## 23. Plain paratha `[assumed — needs dietitian]`
- Ingredients: atta `168893` 50 g; oil `171017` 5 g; salt `173468` 0.5 g; water.
- Cooked yield: 1 paratha; grams **empty until weighed** (`paratha`). Servings: 1 paratha (NIN Annexure 8).

## 24. Puri `[assumed — needs dietitian]`
- Ingredients: atta `168893` 30 g; oil `171017` 12 g (frying oil absorbed is highly variable, a dietitian must decide how much is eaten); salt `173468` 0.3 g.
- Cooked yield: 1 puri; grams **empty until weighed** (`puri`). Servings: 1 puri (NIN Annexure 8).

## 25. Vegetable pulao `[assumed — needs dietitian]`
- Ingredients: rice white raw `169756` 80 g; peas `170419` 20 g; carrot `170393` 20 g; onion `170000` 30 g; oil `171017` 8 g (or ghee `173412` 5 g); cumin `170923` 1 g; salt `173468` 2 g; water.
- Cooked yield: about 300 g. Servings: 1 katori_nin_m.

## 26. Boiled egg `[assumed — needs dietitian]`
- Ingredients: egg `171287` 50 g raw per egg (hard-boiled row `173424` is better when the user logs a cooked egg).
- Servings: 1 egg (`egg_large` 50 g from USDA; Indian eggs are often smaller, see `egg_medium`, `egg_small`).

## 27. Masala omelette `[assumed — needs dietitian]`
- Ingredients: egg `171287` 100 g (2 eggs); onion `170000` 20 g; tomato `170457` 15 g; oil `171017` 5 g; salt `173468` 1 g.
- Cooked yield: about 120 g. Servings: 1 omelette (2 eggs).

## 28. Besan chilla `[assumed — needs dietitian]`
- Ingredients: besan `174288` 50 g; onion `170000` 25 g; tomato `170457` 20 g; oil `171017` 5 g; turmeric `172231` 0.3 g; salt `173468` 1 g; water.
- Cooked yield: about 2 chillas; grams per chilla **empty until weighed**. Servings: 2 chillas.

## 29. Cucumber raita `[assumed — needs dietitian]`
- Ingredients: curd `171284` 120 g; cucumber `169225` 40 g; cumin `170923` 0.3 g; salt `173468` 0.8 g.
- Cooked yield: about 160 g. Servings: 1 katori_nin_s.

## 30. Sweet lassi `[assumed — needs dietitian]`
- Ingredients: curd `171284` 150 g; water 100 g; sugar `169655` 15 g.
- Cooked yield: about 265 g. Servings: 1 glass (250 ml, `glass`; unverified size).

---

## What a dietitian should settle

1. Replace `[assumed]` with a cited recipe source (IFCT/NIN recipe tables after permission, or a university recipe book) and weigh test batches for every yield.
2. Weigh piece-type foods (roti, phulka, paratha, idli, dosa, puri, vada, samosa, laddoo) for the empty `grams` cells in `household_units.csv`.
3. Add FDC-independent rows for the GAP items (paneer, poha, jaggery, curry leaves).
4. Decide the katori default (150 ml vs NIN 200 ml).
