# UAsset Text Extractor - Công cụ trích xuất và dịch text từ file .uasset

## Mô tả
Đây là công cụ Python để trích xuất text từ file .uasset của Unreal Engine và cho phép import lại sau khi chỉnh sửa/dịch thuật.

## Tính năng
- ✅ Trích xuất text có ý nghĩa từ file .uasset
- ✅ Phát hiện ngôn ngữ tự động (Tiếng Việt, Anh, Pháp, Đức, Ý, Tây Ban Nha, Nhật, Hàn, Trung)
- ✅ Xuất ra file JSON để chỉnh sửa dễ dàng
- ✅ Import lại và tạo file .uasset mới với text đã dịch
- ✅ Lọc thông minh để chỉ lấy text có ý nghĩa

## Cài đặt
```bash
# Không cần cài đặt thêm gì, chỉ cần Python 3.6+
python3 --version
```

## Cách sử dụng

### 1. Trích xuất text từ file .uasset đơn lẻ

```bash
python3 uasset_text_extractor.py extract GDSSystemText.uasset
```

Hoặc chỉ định file đầu ra:

```bash
python3 uasset_text_extractor.py extract GDSSystemText.uasset -o my_texts.json
```

### 2. Trích xuất tất cả file .uasset trong folder hiện tại (Batch Extract)

```bash
python3 uasset_text_extractor.py batch-extract
```

Lệnh này sẽ:
- Tự động tìm tất cả file `.uasset` trong folder hiện tại
- **Tự động tìm thêm file `.uasset` trong folder `original` nếu có**
- Tạo folder `extract` nếu chưa có
- Trích xuất text từ mỗi file và lưu vào folder `extract` với tên `[tên_file]_texts.json`
- Hiển thị tiến trình và kết quả cho từng file

### 3. Chỉnh sửa text

Mở file JSON được tạo ra (ví dụ: `extract/GDSSystemText_texts.json`) và chỉnh sửa trường `translated_text` trong các entry:

```json
{
  "id": 1,
  "key": "example_key",
  "original_text": "Exit Craft Mode",
  "translated_text": "Thoát chế độ chế tạo",
  "language": "english",
  "position": 12345
}
```

### 4. Import text đã chỉnh sửa từ file đơn lẻ

```bash
python3 uasset_text_extractor.py import extract/GDSSystemText_texts.json
```

Hoặc chỉ định file đầu ra:

```bash
python3 uasset_text_extractor.py import extract/GDSSystemText_texts.json -o translated_file.uasset
```

### 5. Import tất cả file từ folder extract (Batch Import)

```bash
python3 uasset_text_extractor.py batch-import
```

Lệnh này sẽ:
- Tự động tìm tất cả file JSON trong folder `extract`
- Tạo folder `import` nếu chưa có
- Tạo file `.uasset` mới cho mỗi file JSON với tên `[tên_file]_translated.uasset`
- Lưu tất cả file đã dịch vào folder `import`
- Hiển thị tiến trình và kết quả cho từng file

## Workflow đề xuất cho dự án dịch thuật

### Bước 1: Trích xuất tất cả text
```bash
python3 uasset_text_extractor.py batch-extract
```

### Bước 2: Dịch thuật
- Mở các file JSON trong folder `extract`
- Chỉnh sửa trường `translated_text` cho từng entry
- Có thể sử dụng công cụ dịch tự động hoặc dịch thủ công

### Bước 3: Tạo file game đã dịch
```bash
python3 uasset_text_extractor.py batch-import
```

### Bước 4: Sử dụng file đã dịch
- Copy các file từ folder `import` vào game
- Backup file gốc trước khi thay thế

## Cấu trúc thư mục sau khi sử dụng

```
DichGame/
├── original/                    # Folder chứa file .uasset gốc (tùy chọn)
│   ├── GDSSystemText.uasset
│   ├── GDSTipsText.uasset
│   └── ...
├── extract/                     # Folder chứa file JSON đã trích xuất
│   ├── GDSSystemText_texts.json
│   ├── GDSTipsText_texts.json
│   └── ...
├── import/                      # Folder chứa file .uasset đã dịch
│   ├── GDSSystemText_translated.uasset
│   ├── GDSTipsText_translated.uasset
│   └── ...
├── [file .uasset gốc khác]
├── uasset_text_extractor.py
├── demo_translation.py
└── README.md
```

## Dịch tự động bằng Google Gemini AI

### Cài đặt thư viện
```bash
pip3 install -r requirements.txt
```

### Cài đặt API Key
```bash
# Cách 1: Biến môi trường (khuyến nghị)
export GEMINI_API_KEY='your-api-key-here'

# Cách 2: Truyền trực tiếp
python3 auto_translator.py translate file.json --api-key your-api-key-here
```

### Dịch một file JSON
```bash
python3 auto_translator.py translate extract/GDSSystemText_texts.json
```

### Dịch tất cả file trong folder extract
```bash
python3 auto_translator.py batch
```

### Tính năng của Auto Translator
- **🤖 AI Translation**: Sử dụng Google Gemini Pro để dịch tự nhiên
- **📚 Dictionary**: Ưu tiên sử dụng từ điển `tudien.json`
- **💾 Smart Cache**: Lưu cache để tránh dịch lại
- **📊 Progress Tracking**: Hiển thị tiến trình và thống kê
- **⚡ Rate Limiting**: Tự động delay để tránh vượt giới hạn API

### Demo nhanh
Chạy demo để xem cách dịch thủ công:
```bash
python3 demo_translation.py
```

## Cấu trúc file JSON

```json
{
  "file_info": {
    "original_file": "/path/to/original.uasset",
    "file_size": 14294,
    "total_entries": 148
  },
  "text_entries": [
    {
      "id": 0,
      "key": "text_entry_0",
      "original_text": "Exit Craft Mode?",
      "translated_text": "Thoát chế độ xây dựng?",
      "language": "english",
      "position": 1260,
      "length": 16
    }
  ]
}
```

### Giải thích các trường:
- `id`: ID duy nhất của text entry
- `key`: Key/identifier được phát hiện (nếu có)
- `original_text`: Text gốc từ file .uasset
- `translated_text`: Text đã dịch (chỉnh sửa trường này)
- `language`: Ngôn ngữ được phát hiện tự động
- `position`: Vị trí trong file gốc
- `length`: Độ dài của text

## Lưu ý quan trọng

### ⚠️ Backup file gốc
Luôn backup file .uasset gốc trước khi thay thế!

### ⚠️ Độ dài text
- Text dịch không nên dài hơn quá nhiều so với text gốc
- Nếu text dịch ngắn hơn: OK
- Nếu text dịch dài hơn nhiều: có thể gây lỗi game

### ⚠️ Ký tự đặc biệt
- Giữ nguyên các ký tự đặc biệt như `\n`, `\r`
- Không thay đổi các placeholder như `{0}`, `{1}`

## Ví dụ dịch thuật

### Tiếng Anh -> Tiếng Việt
```json
{
  "original_text": "Exit Craft Mode?",
  "translated_text": "Thoát chế độ xây dựng?"
},
{
  "original_text": "Enter a gift code.",
  "translated_text": "Nhập mã quà tặng."
},
{
  "original_text": "Communication failed.",
  "translated_text": "Kết nối thất bại."
}
```

## Xử lý lỗi

### Lỗi "Không tìm thấy file .uasset gốc"
- Đảm bảo file .uasset gốc vẫn tồn tại
- Kiểm tra đường dẫn trong file JSON

### Lỗi "Text quá dài"
- Rút ngắn text dịch
- Hoặc sử dụng từ viết tắt

### Game không nhận file mới
- Kiểm tra tên file có đúng không
- Đảm bảo file có quyền đọc/ghi
- Thử restart game

## Các file được tạo

1. `[tên_file]_texts.json` - File JSON chứa text để chỉnh sửa
2. `[tên_file]_translated.uasset` - File .uasset mới với text đã dịch

## Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra file có đúng format .uasset không
2. Đảm bảo Python 3.6+ được cài đặt
3. Kiểm tra quyền đọc/ghi file
4. Backup và thử lại với file nhỏ hơn

## Giới hạn

- Chỉ hỗ trợ file .uasset text-based
- Không hỗ trợ file binary phức tạp
- Text dịch quá dài có thể gây lỗi
- Một số ký tự đặc biệt có thể không được hỗ trợ

---

**Chúc bạn dịch game vui vẻ! 🎮**