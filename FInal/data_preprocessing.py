"""
Phân tích chiến thuật bóng đá World Cup 2018 bằng FP-Growth
Nguồn dữ liệu: StatsBomb Open Data
Cài đặt:
    pip install statsbombpy pandas mlxtend openpyxl

Chạy:
    python wc2018_fpgrowth_pipeline.py

Kết quả xuất ra:
    wc2018_matches.csv
    wc2018_events_selected.csv
    wc2018_fp_transactions.csv
    wc2018_frequent_itemsets.csv
    wc2018_association_rules.csv
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
from statsbombpy import sb
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, association_rules


COMPETITION_ID = 43
SEASON_ID = 3

MIN_SUPPORT = 0.03
MIN_CONFIDENCE = 0.35
MAX_LEN = 5


def safe_bool(value):
    if pd.isna(value):
        return False
    return bool(value)


def zone_from_location(loc):
    """
    StatsBomb dùng sân 120 x 80.
    Chia sân thành 3 dọc:
    - Defensive third: x < 40
    - Middle third: 40 <= x < 80
    - Attacking third: x >= 80
    Và 3 ngang:
    - Left: y < 26.67
    - Centre: 26.67 <= y < 53.33
    - Right: y >= 53.33
    """
    if not isinstance(loc, list) or len(loc) < 2:
        return "zone=unknown"

    x, y = loc[0], loc[1]

    if x < 40:
        vertical = "defensive_third"
    elif x < 80:
        vertical = "middle_third"
    else:
        vertical = "attacking_third"

    if y < 26.67:
        horizontal = "left"
    elif y < 53.33:
        horizontal = "centre"
    else:
        horizontal = "right"

    return f"zone={vertical}_{horizontal}"


def event_to_items(row):
    items = []

    team = row.get("team")
    if pd.notna(team):
        items.append(f"team={team}")

    ev_type = row.get("type")
    if pd.notna(ev_type):
        items.append(f"event={ev_type}")

    play_pattern = row.get("play_pattern")
    if pd.notna(play_pattern):
        items.append(f"play_pattern={play_pattern}")

    position = row.get("position")
    if pd.notna(position):
        items.append(f"position={position}")

    items.append(zone_from_location(row.get("location")))

    if safe_bool(row.get("under_pressure")):
        items.append("under_pressure=yes")

    if ev_type == "Pass":
        pass_height = row.get("pass_height")
        if pd.notna(pass_height):
            items.append(f"pass_height={pass_height}")

        pass_body_part = row.get("pass_body_part")
        if pd.notna(pass_body_part):
            items.append(f"pass_body_part={pass_body_part}")

        pass_outcome = row.get("pass_outcome")
        if pd.isna(pass_outcome):
            items.append("pass_outcome=Complete")
        else:
            items.append(f"pass_outcome={pass_outcome}")

        if safe_bool(row.get("pass_cross")):
            items.append("pass_cross=yes")

        if safe_bool(row.get("pass_switch")):
            items.append("pass_switch=yes")

        if safe_bool(row.get("pass_cut_back")):
            items.append("pass_cut_back=yes")

        pass_type = row.get("pass_type")
        if pd.notna(pass_type):
            items.append(f"pass_type={pass_type}")

    if ev_type == "Carry":
        carry_end = row.get("carry_end_location")
        items.append(zone_from_location(carry_end).replace("zone=", "carry_end_zone="))

    if ev_type == "Shot":
        shot_outcome = row.get("shot_outcome")
        if pd.notna(shot_outcome):
            items.append(f"shot_outcome={shot_outcome}")

        shot_body_part = row.get("shot_body_part")
        if pd.notna(shot_body_part):
            items.append(f"shot_body_part={shot_body_part}")

        shot_technique = row.get("shot_technique")
        if pd.notna(shot_technique):
            items.append(f"shot_technique={shot_technique}")

    if ev_type in ["Pressure", "Duel", "Interception", "Block", "Clearance"]:
        items.append("defensive_action=yes")

    return sorted(set(items))


def main():
    print("Đang tải danh sách trận World Cup 2018 từ StatsBomb...")
    matches = sb.matches(competition_id=COMPETITION_ID, season_id=SEASON_ID)
    matches.to_csv("wc2018_matches.csv", index=False, encoding="utf-8-sig")
    print(f"Số trận: {len(matches)}")

    all_events = []
    for i, match_id in enumerate(matches["match_id"].tolist(), start=1):
        print(f"Tải events trận {i}/{len(matches)}: match_id={match_id}")
        ev = sb.events(match_id=match_id)
        ev["match_id"] = match_id
        all_events.append(ev)

    events = pd.concat(all_events, ignore_index=True)

    selected_cols = [
        "match_id", "id", "index", "period", "timestamp", "minute", "second",
        "team", "possession", "possession_team", "type", "play_pattern",
        "player", "position", "location", "under_pressure",
        "pass_height", "pass_body_part", "pass_outcome", "pass_type",
        "pass_cross", "pass_switch", "pass_cut_back",
        "carry_end_location",
        "shot_outcome", "shot_body_part", "shot_technique"
    ]
    selected_cols = [c for c in selected_cols if c in events.columns]
    events_selected = events[selected_cols].copy()
    events_selected.to_csv("wc2018_events_selected.csv", index=False, encoding="utf-8-sig")

    print("Đang tạo transaction theo từng possession...")
    transactions = []
    for (match_id, team, possession), g in events_selected.groupby(["match_id", "team", "possession"], dropna=True):
        basket = []
        for _, row in g.iterrows():
            basket.extend(event_to_items(row))
        basket = sorted(set(basket))

        if len(basket) >= 3:
            transactions.append({
                "match_id": match_id,
                "team": team,
                "possession": possession,
                "items": "|".join(basket)
            })

    trans_df = pd.DataFrame(transactions)
    trans_df.to_csv("wc2018_fp_transactions.csv", index=False, encoding="utf-8-sig")
    print(f"Số transaction: {len(trans_df)}")

    transaction_lists = trans_df["items"].str.split("|").tolist()

    te = TransactionEncoder()
    onehot = te.fit(transaction_lists).transform(transaction_lists)
    onehot_df = pd.DataFrame(onehot, columns=te.columns_)

    print("Chạy FP-Growth...")
    print(f"MAX_LEN = {MAX_LEN}")
    frequent_itemsets = fpgrowth(onehot_df, min_support=MIN_SUPPORT, use_colnames=True, max_len=MAX_LEN)
    frequent_itemsets["length"] = frequent_itemsets["itemsets"].apply(len)
    frequent_itemsets = frequent_itemsets.sort_values(["support", "length"], ascending=[False, False])
    frequent_itemsets["itemsets"] = frequent_itemsets["itemsets"].apply(lambda x: " | ".join(sorted(list(x))))
    frequent_itemsets.to_csv("wc2018_frequent_itemsets.csv", index=False, encoding="utf-8-sig")

    print("Xong.")
    frequent_for_rules = fpgrowth(onehot_df, min_support=MIN_SUPPORT, use_colnames=True, max_len=MAX_LEN)
    rules = association_rules(frequent_for_rules, metric="confidence", min_threshold=MIN_CONFIDENCE)
    if not rules.empty:
        rules = rules.sort_values(["lift", "confidence", "support"], ascending=False)
        rules["antecedents"] = rules["antecedents"].apply(lambda x: " | ".join(sorted(list(x))))
        rules["consequents"] = rules["consequents"].apply(lambda x: " | ".join(sorted(list(x))))
    rules.to_csv("wc2018_association_rules.csv", index=False, encoding="utf-8-sig")

    print("Hoàn tất.")



if __name__ == "__main__":
    main()
