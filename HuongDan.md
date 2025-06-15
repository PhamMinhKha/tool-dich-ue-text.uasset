# 🚀 Hướng Dẫn Sử Dụng Auto Translator

## 📋 Tổng Quan

`auto_translator.py` là công cụ dịch tự động các file JSON đã extract từ game sang tiếng Việt sử dụng Google Gemini API. Chương trình hỗ trợ dịch từng file hoặc dịch hàng loạt với hệ thống cache và từ điển thông minh.

## 🔧 Cài Đặt Ban Đầu

### 1️⃣ Cài đặt thư viện
```bash
pip install -r requirements.txt
```

### 2️⃣ Lấy API Key từ Google AI Studio

#### Phương pháp 1: Sử dụng nhiều API Keys (Khuyến nghị) 🚀
1. Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Tạo nhiều API key từ các tài khoản Google khác nhau
3. Thêm các key vào file `listkey.txt`:
   ```
   AIzaSyABC123...
   AIzaSyDEF456...
   AIzaSyGHI789...
   ```
4. **Lợi ích**: Tự động chuyển đổi khi gặp rate limit, tăng hiệu suất dịch

#### Phương pháp 2: Sử dụng biến môi trường
- Truy cập: https://makersuite.google.com/app/apikey
- Tạo API key mới
- Copy API key

### 3️⃣ Cài đặt API Key
```bash
# Windows
set GEMINI_API_KEY=your-api-key-here

# Linux/Mac
export GEMINI_API_KEY=your-api-key-here
```

⚠️ **Lưu ý bảo mật**: Nên sử dụng biến môi trường thay vì hardcode API key trong code.

## 🎯 Cách Sử Dụng

### Dịch tất cả file trong folder extract/
```bash
python auto_translator.py batch
```

### Dịch một file cụ thể
```bash
python auto_translator.py translate extract/GDSSystemText.json
```

### Chỉ định file đầu ra
```bash
python auto_translator.py translate extract/GDSSystemText.json -o my_translation.json
```

### Sử dụng API key tùy chỉnh
```bash
python auto_translator.py batch --api-key your-api-key-here
```

## 📚 Hệ Thống Từ Điển và Cache

### Từ điển (tudien.json)
- **Ưu tiên cao nhất** - không cần dịch lại
- Format: `{"english_word": "từ_tiếng_việt"}`
- Ví dụ:
```json
{
  "exit": "Thoát",
  "craft": "Chế tạo",
  "build": "Xây dựng",
  "chest": "Rương",
  "options": "Tùy chọn",
  "player": "Người chơi"
}
```

### Cache (translation_cache.json)
- Tự động lưu các từ đã dịch bằng Gemini
- Tránh dịch lại, tiết kiệm API calls
- Tự động tạo khi chạy lần đầu
- Không nên xóa file này

## 📁 Cấu Trúc Thư Mục

```
DichGame/
├── extract/                    # File JSON gốc từ game
├── translated/                 # File JSON đã dịch (tự động tạo)
├── import/                     # File .uasset đã dịch (từ import)
├── original/                   # File .uasset gốc
├── tudien.json                # Từ điển tùy chỉnh
├── translation_cache.json     # Cache tự động
├── auto_translator.py         # Chương trình dịch
└── uasset_text_extractor.py   # Chương trình trích xuất
```

## 🔄 Quy Trình Dịch Hoàn Chỉnh

### Bước 1: Trích xuất text từ game
```bash
# Trích xuất tất cả file .uasset
python uasset_text_extractor.py batch-extract

# Hoặc trích xuất từng file
python uasset_text_extractor.py extract GDSSystemText.uasset
```

### Bước 2: Dịch tự động
```bash
# Dịch tất cả file JSON
python auto_translator.py batch

# Hoặc dịch từng file
python auto_translator.py translate extract/GDSSystemText.json
```

### Bước 3: Tạo file game đã dịch
```bash
# Import tất cả file đã dịch
python uasset_text_extractor.py batch-import

# Hoặc import từng file
python uasset_text_extractor.py import translated/GDSSystemText_vietnamese.json
```

## 📊 Thống Kê và Theo Dõi

Chương trình hiển thị thông tin chi tiết:
- 📝 **Tổng số text**: Số lượng text cần dịch
- 🤖 **Dịch bằng Gemini**: Text dịch mới qua API
- 💾 **Lấy từ cache**: Text đã dịch trước đó
- 📚 **Lấy từ từ điển**: Text có sẵn trong tudien.json
- ⏭️ **Bỏ qua**: Text rỗng hoặc không hợp lệ
- ⏱️ **Thời gian**: Thời gian thực hiện
- ⚡ **Tốc độ**: Trung bình giây/text

## ⚡ Tips Tối Ưu

### 1. Tối ưu từ điển
- Thêm các từ game thường dùng vào `tudien.json`
- Sử dụng chữ thường cho key để tăng tỷ lệ match
- Ví dụ: `"health": "Máu", "mana": "Năng lượng"`

### 2. Quản lý cache
- Không xóa `translation_cache.json`
- File này giúp dịch nhanh hơn ở lần sau
- Có thể backup file cache quan trọng

### 3. Dịch hiệu quả
- Có thể dừng và tiếp tục dịch bất cứ lúc nào
- Kiểm tra file trong `translated/` trước khi import
- Sử dụng batch mode cho nhiều file

### 4. Multiple API Keys
- Sử dụng nhiều API key trong `listkey.txt` để tránh rate limit
- Tự động chuyển đổi key khi gặp quota limit
- Hiển thị API key đang sử dụng trong quá trình dịch

### 5. Rate limiting
- Chương trình có delay 0.5s giữa các API call
- Tránh bị Google giới hạn tốc độ
- Không cần lo về việc spam API

## 🛠️ Sử Dụng Programmatically

```python
from auto_translator import AutoTranslator

# Khởi tạo với API key
translator = AutoTranslator(api_key="your-api-key")

# Dịch một file
translator.translate_json_file(
    "extract/game.json", 
    "translated/game_vn.json"
)

# Dịch tất cả file trong folder
translator.batch_translate_folder("extract")

# Dịch một đoạn text
text, source = translator.translate_text("Hello World")
print(f"Dịch: {text} (từ {source})")

# Kiểm tra thống kê
print(f"Đã dịch: {translator.stats['translated']} text")
```

## 🔍 Demo và Kiểm Tra

### Chạy demo
```bash
python demo_auto_translator.py
```

Demo sẽ:
- Tạo từ điển mẫu nếu chưa có
- Kiểm tra môi trường (Python, thư viện, API key)
- Hiển thị hướng dẫn chi tiết
- Kiểm tra các file và folder cần thiết

### Kiểm tra môi trường
Demo sẽ kiểm tra:
- ✅ Python version
- ✅ Thư viện google-generativeai
- ✅ GEMINI_API_KEY
- ✅ Các file cần thiết
- 📁 Các folder và số lượng file

## 🚨 Xử Lý Lỗi Thường Gặp

### Lỗi API Key
```
❌ Cần có GEMINI_API_KEY
```
**Giải pháp**: Cài đặt biến môi trường hoặc truyền API key

### Lỗi không tìm thấy file
```
❌ Không tìm thấy file: extract/game.json
```
**Giải pháp**: Chạy extract trước khi dịch

### Lỗi thư viện
```
❌ google-generativeai: Chưa cài đặt
```
**Giải pháp**: `pip install -r requirements.txt`

### Lỗi rate limit
```
❌ Lỗi khi dịch: Rate limit exceeded
```
**Giải pháp**: Chờ một lúc rồi chạy lại, cache sẽ giúp bỏ qua text đã dịch

## 📝 Cấu Trúc File JSON

File JSON input có cấu trúc:
```json
{
  "text_entries": [
    {
      "original_text": "Hello",
      "translated_text": "Hello",
      "offset": 1234,
      "length": 5
    }
  ]
}
```

Chương trình sẽ:
- Đọc `translated_text` làm nguồn dịch
- Cập nhật `translated_text` với bản dịch tiếng Việt
- Giữ nguyên các field khác

## 🎮 Ví Dụ Thực Tế

### Dịch game hoàn chỉnh
```bash
# 1. Extract tất cả text từ game
python uasset_text_extractor.py batch-extract

# 2. Dịch tất cả file
python auto_translator.py batch

# 3. Import vào game
python uasset_text_extractor.py batch-import
```

### Dịch từng phần
```bash
# Dịch chỉ file system text
python auto_translator.py translate extract/GDSSystemText.json

# Import file đó
python uasset_text_extractor.py import translated/GDSSystemText_vietnamese.json
```

## 🎯 Kết Luận

Auto Translator là công cụ mạnh mẽ để dịch game với:
- ✅ Hỗ trợ cache và từ điển thông minh
- ✅ Dịch hàng loạt hiệu quả
- ✅ Thống kê chi tiết
- ✅ Xử lý lỗi tốt
- ✅ Dễ sử dụng và tùy chỉnh

**Sẵn sàng dịch game của bạn!** 🎮

---

*Tạo bởi Auto Translator Tool - Dịch game tự động với AI*