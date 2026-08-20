import json
from collections import Counter

with open("data/previsions_orages.json", encoding="utf-8") as f:
    data = json.load(f)

top_fl_values = [feat["properties"]["top_cb_fl"] for feat in data["features"]]
print("Nombre total de features :", len(data["features"]))
print("Nombre de features avec top_cb_fl = 0 :", sum(1 for v in top_fl_values if v == 0))
print("Répartition des valeurs de top_cb_fl :")
for val, count in Counter(top_fl_values).most_common(10):
    print(f"  {val} FL : {count} features")

print("\nExemples de features avec risque > 0 :")
count_examples = 0
for feat in data["features"]:
    if feat["properties"]["risque"] > 0:
        print(f"  Risque={feat['properties']['risque']}, Top CB={feat['properties']['top_cb_fl']} FL, Cape={feat['properties']['cape_ml_jkg']}, Precip={feat['properties']['precip_mm_h']}")
        count_examples += 1
        if count_examples >= 5:
            break