# ⚽ Phân tích chiến thuật bóng đá World Cup 2018 bằng FP-Growth

## Giới thiệu

Dự án thực hiện khai phá dữ liệu sự kiện bóng đá từ bộ dữ liệu **StatsBomb Open Data – FIFA World Cup 2018** nhằm phát hiện các mẫu chiến thuật xuất hiện lặp lại trong các trận đấu.

Nghiên cứu sử dụng:

* Frequent Pattern Mining
* Association Rule Mining
* Thuật toán FP-Growth

để phân tích các pha kiểm soát bóng (Possession) và tìm ra những đặc điểm chiến thuật phổ biến trong giải đấu.

---

# Mục tiêu

Các mục tiêu chính của dự án bao gồm:

* Chuyển đổi dữ liệu sự kiện bóng đá thành transaction theo possession.
* Tìm các frequent itemsets xuất hiện thường xuyên.
* Sinh association rules để phát hiện mối liên hệ giữa các đặc trưng chiến thuật.
* Phân tích các mẫu kiểm soát bóng, phát bóng lên, pressing và tình huống cố định.
* Phân tích riêng các possession kết thúc bằng cú sút (Shot) nhằm tìm hiểu cách tạo cơ hội ghi bàn.

---

# Nguồn dữ liệu

Nguồn dữ liệu:

**StatsBomb Open Data**

Giải đấu:

* FIFA World Cup 2018
* Competition ID = 43
* Season ID = 3

---

# Thống kê dữ liệu

| Thông tin                   | Giá trị |
| --------------------------- | ------- |
| Số trận đấu                 | 64      |
| Số đội tuyển                | 32      |
| Số sự kiện được chọn        | 227.825 |
| Số possession (transaction) | 20.963  |
| Số frequent itemsets        | 359.247 |
| Số association rules        | 589.867 |

---

# Cấu trúc thư mục

```text
.
├── data_preprocessing.py
├── analysis_report.py
├── shot_analysis.py
│
├── wc2018_matches.csv
├── wc2018_events_selected.csv
├── wc2018_fp_transactions.csv
├── wc2018_frequent_itemsets.csv
├── wc2018_association_rules.csv
│
├── wc2018_shot_transactions.csv
├── wc2018_shot_itemsets.csv
│
├── report_bar_charts/
└── README.md
```

---

# Quy trình thực hiện

## Bước 1: Tiền xử lý dữ liệu

File:

```python
data_preprocessing.py
```

Chức năng:

* Tải dữ liệu World Cup 2018 từ StatsBomb.
* Chọn các thuộc tính phục vụ phân tích chiến thuật.
* Chuẩn hóa dữ liệu.
* Xuất dữ liệu trung gian.

Kết quả:

```text
wc2018_matches.csv
wc2018_events_selected.csv
```

---

## Bước 2: Xây dựng transaction theo possession

Mỗi possession được xem như một transaction.

Các item được tạo từ:

* Loại sự kiện (Pass, Carry, Shot, ...)
* Play Pattern
* Vị trí cầu thủ
* Khu vực sân bóng
* Đặc điểm đường chuyền
* Kỹ thuật dứt điểm
* Trạng thái bị gây áp lực

Ví dụ:

```text
event=Pass
play_pattern=Regular Play
zone=middle_third_centre
under_pressure=yes
pass_outcome=Complete
```

Kết quả:

```text
wc2018_fp_transactions.csv
```

---

## Bước 3: Khai phá Frequent Itemsets và Association Rules

File:

```python
analysis_report.py
```

Thuật toán:

```text
FP-Growth
```

Tham số:

```python
MIN_SUPPORT = 0.03
MIN_CONFIDENCE = 0.35
MAX_LEN = 5
```

Kết quả:

```text
wc2018_frequent_itemsets.csv
wc2018_association_rules.csv
```

---

# Một số kết quả nổi bật

## Frequent Itemsets phổ biến nhất

| Itemset                   | Support |
| ------------------------- | ------- |
| event=Pass                | 62.10%  |
| under_pressure=yes        | 59.49%  |
| event=Ball Receipt*       | 56.58%  |
| defensive_action=yes      | 54.86%  |
| play_pattern=Regular Play | 52.01%  |
| event=Carry               | 49.04%  |

Kết quả cho thấy phần lớn possession trong World Cup 2018 được xây dựng dựa trên chuỗi hành động:

```text
Nhận bóng
→ Chuyền bóng
→ Di chuyển bóng
```

---

## Association Rules nổi bật

Luật có Lift cao nhất:

```text
pass_height=High Pass
+
play_pattern=From Goal Kick
+
position=Goalkeeper
→
pass_type=Goal Kick
```

Chỉ số:

| Chỉ số     | Giá trị |
| ---------- | ------- |
| Support    | 3.07%   |
| Confidence | 95.41%  |
| Lift       | 28.53   |

Kết quả cho thấy các tình huống phát bóng lên thường được thực hiện bởi thủ môn thông qua các đường chuyền dài.

Đây là mẫu chiến thuật ổn định nhất được phát hiện trong dữ liệu.

---

# Phân tích Possession kết thúc bằng Shot

File:

```python
shot_analysis.py
```

Mục tiêu:

Lọc riêng các possession chứa sự kiện:

```text
event=Shot
```

để nghiên cứu cách tạo ra cơ hội dứt điểm.

Sau khi lọc:

| Thông tin          | Giá trị |
| ------------------ | ------- |
| Tổng possession    | 20.963  |
| Possession có Shot | 1.568   |
| Tỷ lệ              | 7.48%   |

---

## Frequent Itemsets phổ biến trong Shot Possession

| Itemset                     | Support |
| --------------------------- | ------- |
| event=Shot                  | 100%    |
| event=Pass                  | 90.63%  |
| zone=attacking_third_centre | 89.22%  |
| event=Ball Receipt*         | 88.46%  |
| shot_technique=Normal       | 85.33%  |
| pass_outcome=Complete       | 85.27%  |

Kết quả cho thấy:

* Phần lớn cơ hội dứt điểm được tạo ra sau các đường chuyền thành công.
* Các cú sút chủ yếu xuất hiện ở khu vực trung tâm của 1/3 sân tấn công.
* Chuỗi nhận bóng → chuyền bóng → dứt điểm là cấu trúc phổ biến nhất.

---

# Thư viện sử dụng

```text
pandas
numpy
matplotlib
statsbombpy
mlxtend
openpyxl
```

Cài đặt:

```bash
pip install pandas numpy matplotlib statsbombpy mlxtend openpyxl
```

---

# Kết luận

Dự án cho thấy thuật toán FP-Growth có khả năng phát hiện hiệu quả các mẫu chiến thuật trong dữ liệu bóng đá.

Các kết quả thu được phản ánh:

* Cấu trúc kiểm soát bóng phổ biến.
* Hành vi triển khai bóng từ thủ môn.
* Tác động của pressing.
* Đặc điểm của các pha tạo cơ hội dứt điểm.

Qua đó chứng minh khả năng ứng dụng của khai phá dữ liệu trong phân tích chiến thuật bóng đá hiện đại.

---

## Tác giả

Nguyễn Văn Hướng
Nguyễn Quốc Bảo
Vũ Tuấn Khanh

## Đề tài:

**Phân tích chiến thuật bóng đá World Cup 2018 bằng FP-Growth và Association Rule Mining**
