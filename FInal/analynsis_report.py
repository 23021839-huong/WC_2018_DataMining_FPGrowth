from pathlib import Path
import textwrap
import pandas as pd
import matplotlib.pyplot as plt

# ===============================
# File đầu vào
# ===============================

EVENTS_FILE = "wc2018_events_selected.csv"
TRANSACTIONS_FILE = "wc2018_fp_transactions.csv"
FREQUENT_ITEMSETS_FILE = "wc2018_frequent_itemsets.csv"
ASSOCIATION_RULES_FILE = "wc2018_association_rules.csv"

OUTPUT_DIR = Path("report_bar_charts")

# ===============================
# Hàm kiểm tra file
# ===============================

def check_file(path):
    if not Path(path).exists():
        print(f"Không tìm thấy file: {path}")
        return False
    return True

# ===============================
# Hàm xuống dòng label
# ===============================

def wrap_labels(labels, width=25):
    return [
        "\n".join(textwrap.wrap(str(label), width=width))
        for label in labels
    ]

# ===============================
# Hàm vẽ biểu đồ chung
# ===============================

def save_bar_chart(
    series,
    title,
    xlabel,
    ylabel,
    output_file,
    horizontal=False,
    top_n=None
):

    if series is None or len(series) == 0:
        print(f"Không có dữ liệu: {output_file}")
        return

    if top_n:
        series = series.head(top_n)

    plt.figure(figsize=(12, 7))

    if horizontal:

        values = series.values[::-1]
        labels = wrap_labels(
            series.index[::-1],
            width=35
        )

        plt.barh(labels, values)

        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

    else:

        values = series.values
        labels = wrap_labels(
            series.index,
            width=18
        )

        plt.bar(labels, values)

        plt.xlabel(xlabel)
        plt.ylabel(ylabel)

        plt.xticks(
            rotation=35,
            ha="right"
        )

    plt.title(title)

    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / output_file,
        dpi=300,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Đã tạo: {output_file}")

# ===============================
# 1. Event Counts
# ===============================

def chart_event_counts():

    if not check_file(EVENTS_FILE):
        return

    df = pd.read_csv(EVENTS_FILE)

    if "type" not in df.columns:
        return

    series = (
        df["type"]
        .dropna()
        .value_counts()
        .head(15)
    )

    save_bar_chart(
        series,
        "Top 15 loại sự kiện xuất hiện nhiều nhất",
        "Loại sự kiện",
        "Số lần",
        "event_counts.png"
    )

# ===============================
# 2. Play Pattern
# ===============================

def chart_play_patterns():

    if not check_file(EVENTS_FILE):
        return

    df = pd.read_csv(EVENTS_FILE)

    if "play_pattern" not in df.columns:
        return

    series = (
        df["play_pattern"]
        .dropna()
        .value_counts()
    )

    save_bar_chart(
        series,
        "Phân bố Play Pattern",
        "Play Pattern",
        "Số lần",
        "play_patterns.png"
    )

# ===============================
# 3. Team Transactions
# ===============================

def chart_team_transactions():

    if not check_file(TRANSACTIONS_FILE):
        return

    df = pd.read_csv(TRANSACTIONS_FILE)

    if "team" not in df.columns:
        return

    series = (
        df["team"]
        .dropna()
        .value_counts()
        .head(20)
    )

    save_bar_chart(
        series,
        "Top 20 đội có nhiều transaction nhất",
        "Đội bóng",
        "Số transaction",
        "team_transactions.png"
    )

# ===============================
# 4. Itemset Length Distribution
# ===============================

def chart_itemset_length_distribution():

    if not check_file(FREQUENT_ITEMSETS_FILE):
        return

    df = pd.read_csv(FREQUENT_ITEMSETS_FILE)

    if "length" not in df.columns:

        if "itemsets" not in df.columns:
            return

        df["length"] = (
            df["itemsets"]
            .astype(str)
            .apply(
                lambda x: len(
                    [
                        i
                        for i in x.split("|")
                        if i.strip()
                    ]
                )
            )
        )

    series = (
        df["length"]
        .value_counts()
        .sort_index()
    )

    series.index = [
        f"{i} item"
        for i in series.index
    ]

    save_bar_chart(
        series,
        "Phân bố độ dài Frequent Itemsets",
        "Độ dài Itemset",
        "Số lượng",
        "itemset_length_distribution.png"
    )

# ===============================
# 5. Top Itemsets Support
# ===============================

def chart_top10_frequent_itemsets_support():

    if not check_file(FREQUENT_ITEMSETS_FILE):
        return

    df = pd.read_csv(FREQUENT_ITEMSETS_FILE)

    if (
        "itemsets" not in df.columns
        or
        "support" not in df.columns
    ):
        return

    top10 = (
        df.sort_values(
            "support",
            ascending=False
        )
        .head(10)
    )

    labels = (
        top10["itemsets"]
        .astype(str)
        .apply(
            lambda x:
            x[:70] + "..."
            if len(x) > 70
            else x
        )
    )

    series = pd.Series(
        top10["support"].values,
        index=labels
    )

    save_bar_chart(
        series,
        "Top 10 Frequent Itemsets Theo Support",
        "Support",
        "Frequent Itemsets",
        "top10_frequent_itemsets_support.png",
        horizontal=True
    )

# ===============================
# 6. Xuất Top Rules
# ===============================

def export_top10_association_rules():

    if not check_file(ASSOCIATION_RULES_FILE):
        return

    df = pd.read_csv(ASSOCIATION_RULES_FILE)

    required = [
        "antecedents",
        "consequents",
        "support",
        "confidence",
        "lift"
    ]

    for col in required:
        if col not in df.columns:
            print(f"Thiếu cột {col}")
            return

    top10 = (
        df.sort_values(
            ["lift", "confidence"],
            ascending=False
        )
        .head(10)
    )

    output_excel = (
        OUTPUT_DIR /
        "top10_association_rules.xlsx"
    )

    top10[
        [
            "antecedents",
            "consequents",
            "support",
            "confidence",
            "lift"
        ]
    ].to_excel(
        output_excel,
        index=False
    )

    print(
        "Đã tạo:",
        output_excel
    )

# ===============================
# MAIN
# ===============================

def main():

    OUTPUT_DIR.mkdir(
        exist_ok=True
    )

    print("=" * 50)
    print("BẮT ĐẦU PHÂN TÍCH")
    print("=" * 50)

    chart_event_counts()

    chart_play_patterns()

    chart_team_transactions()

    chart_itemset_length_distribution()

    chart_top10_frequent_itemsets_support()

    export_top10_association_rules()

    print("\nHoàn tất.")
    print(
        "Kết quả nằm trong:",
        OUTPUT_DIR.resolve()
    )

if __name__ == "__main__":
    main()