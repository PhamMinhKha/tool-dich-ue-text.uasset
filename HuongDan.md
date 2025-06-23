# 🚀 Hướng Dẫn Sử Dụng Auto Translator

## 📋 Tổng Quan

`auto_translator.py` là công cụ dịch tự động các file JSON đã extract từ game sang tiếng Việt sử dụng Google Gemini API hoặc ChatGPT API. Chương trình hỗ trợ dịch từng file hoặc dịch hàng loạt với hệ thống cache và từ điển thông minh.

### 🤖 AI Engines Hỗ Trợ
- **Google Gemini** (mặc định): Sử dụng Gemini Pro model
- **ChatGPT**: Sử dụng GPT-3.5-turbo model

## 🔧 Cài Đặt Ban Đầu

### 1️⃣ Cài đặt thư viện
```bash
pip install -r requirements.txt
```

**Thư viện cần thiết:**
- `google-generativeai`: Cho Gemini API
- `openai`: Cho ChatGPT API (tùy chọn)
- Các thư viện khác: `json`, `os`, `time`, `argparse`

### 2️⃣ Lấy API Key

#### 🔹 Google Gemini API Key

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

#### 🔹 ChatGPT API Key
1. Truy cập [OpenAI Platform](https://platform.openai.com/api-keys)
2. Đăng nhập hoặc tạo tài khoản OpenAI
3. Tạo API key mới
4. Copy API key
5. **Lưu ý**: Cần có credit trong tài khoản OpenAI để sử dụng API

### 3️⃣ Cài đặt API Key

#### Cho Google Gemini:
```bash
# Windows
set GEMINI_API_KEY=your-gemini-key-here

# Linux/Mac
export GEMINI_API_KEY=your-gemini-key-here
```

#### Cho ChatGPT:
```bash
# Windows
set OPENAI_API_KEY=your-openai-key-here

# Linux/Mac
export OPENAI_API_KEY=your-openai-key-here
```

⚠️ **Lưu ý bảo mật**: Nên sử dụng biến môi trường thay vì hardcode API key trong code.

## 🎯 Cách Sử Dụng

### Dịch tất cả file trong folder extract/
```bash
# Sử dụng Gemini (mặc định)
python auto_translator.py batch

# Sử dụng ChatGPT
python auto_translator.py batch --ai-engine chatgpt
```

### Dịch một file cụ thể
```bash
# Với Gemini
python auto_translator.py translate extract/GDSSystemText.json

# Với ChatGPT
python auto_translator.py translate extract/GDSSystemText.json --ai-engine chatgpt
```

### Chỉ định file đầu ra
```bash
python auto_translator.py translate extract/GDSSystemText.json -o my_translation.json --ai-engine chatgpt
```

### Sử dụng API key tùy chỉnh
```bash
# Với Gemini
python auto_translator.py batch --api-key your-gemini-key-here

# Với ChatGPT
python auto_translator.py batch --api-key your-openai-key-here --ai-engine chatgpt
```

### 🆕 Tham số AI Engine
- `--ai-engine gemini`: Sử dụng Google Gemini (mặc định)
- `--ai-engine chatgpt`: Sử dụng ChatGPT GPT-3.5-turbo

### 🔄 So Sánh AI Engines

| Tiêu chí | Google Gemini | ChatGPT |
|----------|---------------|----------|
| **Miễn phí** | ✅ Có quota miễn phí | ❌ Cần trả phí |
| **Tốc độ** | ⚡ Nhanh | ⚡ Nhanh |
| **Chất lượng dịch** | 🎯 Tốt | 🎯 Rất tốt |
| **Hỗ trợ tiếng Việt** | ✅ Tốt | ✅ Rất tốt |
| **Rate limit** | 60 requests/phút | Tùy plan |
| **Setup** | Dễ | Cần credit |

**Khuyến nghị**: 
- Dùng **Gemini** cho dự án cá nhân (miễn phí)
- Dùng **ChatGPT** cho chất lượng dịch cao hơn (có phí)

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
- 🤖 **Dịch bằng AI**: Text dịch mới qua API (hiển thị engine: GEMINI hoặc CHATGPT)
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

# Khởi tạo với Gemini (mặc định)
translator = AutoTranslator(api_key="your-gemini-key")

# Khởi tạo với ChatGPT
translator = AutoTranslator(api_key="your-openai-key", ai_engine="chatgpt")

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
print(f"Engine: {translator.ai_engine}")
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
❌ Cần có OPENAI_API_KEY
```
**Giải pháp**: Cài đặt biến môi trường phù hợp với AI engine hoặc truyền API key

### Lỗi không tìm thấy file
```
❌ Không tìm thấy file: extract/game.json
```
**Giải pháp**: Chạy extract trước khi dịch

### Lỗi thư viện
```
❌ google-generativeai: Chưa cài đặt
❌ openai: Chưa cài đặt
```
**Giải pháp**: `pip install -r requirements.txt` hoặc `pip install openai` cho ChatGPT

### Lỗi rate limit
```
❌ Lỗi khi dịch: Rate limit exceeded
```
**Giải pháp**: Chờ một lúc rồi chạy lại, cache sẽ giúp bỏ qua text đã dịch

### Lỗi OpenAI API version (ChatGPT)
```
❌ You tried to access openai.ChatCompletion, but this is no longer supported in openai>=1.0.0
```
**Giải pháp**: 
- Cập nhật requirements: `pip install -r requirements.txt`
- Hoặc downgrade: `pip install openai==0.28` (không khuyến nghị)
- Code đã được cập nhật để hỗ trợ OpenAI API v1.0+

### Lỗi ChatGPT trả về format sai

**Vấn đề:** ChatGPT trả về kết quả dạng `"text gốc" -> "bản dịch"` thay vì chỉ bản dịch

**Ví dụ lỗi:**
```json
"Lingua testo": "Lingua testo\" -> \"Ngôn ngữ thử nghiệm"
```

**Nguyên nhân:** ChatGPT có xu hướng trả về format giải thích thay vì chỉ kết quả

**Giải pháp:** 
- Code đã được cập nhật để tự động phát hiện và loại bỏ format sai này
- Prompt đã được tối ưu để ChatGPT chỉ trả về bản dịch
- Thêm logic xử lý để làm sạch output

**Lưu ý:** Nếu vẫn gặp vấn đề, hãy xóa cache và dịch lại

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
- 🆕 **Hỗ trợ 2 AI engines**: Google Gemini và ChatGPT
- 🆕 **Linh hoạt**: Chọn engine phù hợp với nhu cầu và ngân sách

**Sẵn sàng dịch game của bạn với AI tốt nhất!** 🎮🤖

---

*Tạo bởi Auto Translator Tool - Dịch game tự động với AI*