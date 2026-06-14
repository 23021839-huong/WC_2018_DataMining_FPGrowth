import ast
import warnings

warnings.filterwarnings("ignore")

import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth

# =========================
# THAM SỐ
# =========================

EVENTS_FILE = "wc2018_events_selected.csv"

MIN_SUPPORT = 0.05
MAX_LEN = 3

# =========================
# HÀM HỖ TRỢ
# =========================

def safe_bool(value):
    if pd.isna(value):
        return False
    return bool(value)


def parse_location(loc):

    if pd.isna(loc):
        return None

    if isinstance(loc, list):
        return loc

    if isinstance(loc, str):
        try:
            return ast.literal_eval(loc)
        except:
            return None

    return None


def zone_from_location(loc):

    loc = parse_location(loc)

    if loc is None:
        return "zone=unknown"

    if len(loc) < 2:
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


# =========================
# EVENT -> ITEMS
# =========================

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

    items.append(
        zone_from_location(
            row.get("location")
        )
    )

    if safe_bool(
        row.get("under_pressure")
    ):
        items.append(
            "under_pressure=yes"
        )

    # PASS

    if ev_type == "Pass":

        pass_height = row.get(
            "pass_height"
        )

        if pd.notna(pass_height):
            items.append(
                f"pass_height={pass_height}"
            )

        pass_body_part = row.get(
            "pass_body_part"
        )

        if pd.notna(pass_body_part):
            items.append(
                f"pass_body_part={pass_body_part}"
            )

        pass_outcome = row.get(
            "pass_outcome"
        )

        if pd.isna(pass_outcome):
            items.append(
                "pass_outcome=Complete"
            )
        else:
            items.append(
                f"pass_outcome={pass_outcome}"
            )

        if safe_bool(
            row.get("pass_cross")
        ):
            items.append(
                "pass_cross=yes"
            )

        if safe_bool(
            row.get("pass_switch")
        ):
            items.append(
                "pass_switch=yes"
            )

        pass_type = row.get(
            "pass_type"
        )

        if pd.notna(pass_type):
            items.append(
                f"pass_type={pass_type}"
            )

    # CARRY

    if ev_type == "Carry":

        carry_zone = zone_from_location(
            row.get(
                "carry_end_location"
            )
        )

        items.append(
            carry_zone.replace(
                "zone=",
                "carry_end_zone="
            )
        )

    # SHOT

    if ev_type == "Shot":

        shot_outcome = row.get(
            "shot_outcome"
        )

        if pd.notna(
            shot_outcome
        ):
            items.append(
                f"shot_outcome={shot_outcome}"
            )

        shot_technique = row.get(
            "shot_technique"
        )

        if pd.notna(
            shot_technique
        ):
            items.append(
                f"shot_technique={shot_technique}"
            )

    # DEFENSIVE

    if ev_type in [
        "Pressure",
        "Duel",
        "Interception",
        "Block",
        "Clearance"
    ]:
        items.append(
            "defensive_action=yes"
        )

    return sorted(
        list(set(items))
    )


# =========================
# MAIN
# =========================

def main():

    print("Đọc dữ liệu...")

    events = pd.read_csv(
        EVENTS_FILE
    )

    transactions = []

    total_possessions = 0
    shot_possessions = 0

    grouped = events.groupby(
        [
            "match_id",
            "team",
            "possession"
        ],
        dropna=True
    )

    for (
        match_id,
        team,
        possession
    ), g in grouped:

        total_possessions += 1

        # Chỉ giữ possession có Shot

        if "Shot" not in g["type"].values:
            continue

        shot_possessions += 1

        basket = []

        for _, row in g.iterrows():

            basket.extend(
                event_to_items(row)
            )

        basket = sorted(
            list(set(basket))
        )

        if len(basket) >= 3:

            transactions.append(
                {
                    "match_id":
                        match_id,
                    "team":
                        team,
                    "possession":
                        possession,
                    "items":
                        "|".join(
                            basket
                        )
                }
            )

    trans_df = pd.DataFrame(
        transactions
    )

    trans_df.to_csv(
        "wc2018_shot_transactions.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print(
        f"Tổng possession: {total_possessions}"
    )

    print(
        f"Possession có Shot: {shot_possessions}"
    )

    print(
        f"Transaction tạo ra: {len(trans_df)}"
    )

    transaction_lists = (
        trans_df["items"]
        .str.split("|")
        .tolist()
    )

    te = TransactionEncoder()

    onehot = te.fit(
        transaction_lists
    ).transform(
        transaction_lists
    )

    onehot_df = pd.DataFrame(
        onehot,
        columns=te.columns_
    )

    print("Chạy FP-Growth...")

    frequent_itemsets = fpgrowth(
        onehot_df,
        min_support=MIN_SUPPORT,
        use_colnames=True,
        max_len=MAX_LEN
    )

    frequent_itemsets["length"] = (
        frequent_itemsets["itemsets"]
        .apply(len)
    )

    frequent_itemsets["itemsets"] = (
        frequent_itemsets["itemsets"]
        .apply(
            lambda x:
            " | ".join(
                sorted(list(x))
            )
        )
    )

    frequent_itemsets = (
        frequent_itemsets
        .sort_values(
            "support",
            ascending=False
        )
    )

    frequent_itemsets.to_csv(
        "wc2018_shot_itemsets.csv",
        index=False,
        encoding="utf-8-sig"
    )

    print("\nHoàn tất.")

    print("Xuất file:")
    print(" - wc2018_shot_transactions.csv")
    print(" - wc2018_shot_itemsets.csv")


if __name__ == "__main__":
    main()