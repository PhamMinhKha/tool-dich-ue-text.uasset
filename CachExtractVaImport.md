# Hướng Dẫn Extract và Import Text UAsset Bằng Tay với 010 Editor

## Tổng Quan
File `.uasset` của Unreal Engine chứa text được lưu trữ theo 2 định dạng chính:
- **UTF-8**: `<u32 len><string + null terminator>`
- **UTF-16**: `<u32 len_negative><string + null terminator>`

## 1. Xác Định Size Offset Position

### Bước 1: Tìm Size Offset Position
1. Mở file `.uasset` trong 010 Editor
2. Đi đến offset `0x20` (32 decimal)
3. Đọc 4 bytes tiếp theo dưới dạng **Little Endian Integer**
4. Giá trị này chính là `size_offset_position`

**Ví dụ:**
```
Offset 0x20: 4C 1C 01 00
Little Endian: 0x00011C4C = 73,804 decimal
=> size_offset_position = 73,804
```

### Bước 2: Tính File Size
File size được tính theo công thức:
```
file_size = total_file_length - size_offset_position - 104
```

**Ví dụ:**
```
Total file: 150,000 bytes
Size offset: 73,804
File size = 150,000 - 73,804 - 104 = 76,092 bytes
```

## 2. Tìm và Xác Định Text Entries

### 2.1 UTF-8 Text Entry

**Cấu trúc:**
```
[4 bytes: length] [text data] [1 byte: 0x00]
```

**Cách nhận biết:**
1. Đọc 4 bytes đầu dưới dạng Little Endian Integer
2. Nếu giá trị > 0 và < 200, có thể là UTF-8
3. Kiểm tra byte cuối cùng của text có phải 0x00 không
4. Thử decode text để xác nhận

**Ví dụ UTF-8:**
```
Offset: 0x1234
Data: 0C 00 00 00 48 65 6C 6C 6F 20 57 6F 72 6C 64 00

Phân tích:
- Length: 0C 00 00 00 = 12 (bao gồm null terminator)
- Text: "Hello World" (11 ký tự)
- Null terminator: 00
```

### 2.2 UTF-16 Text Entry

**Cấu trúc:**
```
[4 bytes: negative_length] [text data] [2 bytes: 0x00 0x00]
```

**Cách nhận biết:**
1. Đọc 4 bytes đầu dưới dạng Little Endian **Signed** Integer
2. Nếu giá trị < 0, đây là UTF-16
3. Số ký tự thực = -giá_trị_âm
4. Số bytes = số_ký_tự × 2
5. Kiểm tra 2 bytes cuối có phải 0x00 0x00 không

**Ví dụ UTF-16:**
```
Offset: 0x5678
Data: F4 FF FF FF 48 00 65 00 6C 00 6C 00 6F 00 00 00

Phân tích:
- Length: F4 FF FF FF = -12 (signed)
- Số ký tự: 12
- Bytes: 12 × 2 = 24 bytes
- Text: "Hello" (UTF-16LE)
- Null terminator: 00 00
```

## 3. Cách Extract Text Bằng Tay

### Bước 1: Quét File
1. Bắt đầu từ đầu file
2. Tại mỗi vị trí, đọc 4 bytes đầu
3. Kiểm tra xem có phải text entry không:
   - Nếu > 0: kiểm tra UTF-8
   - Nếu < 0: kiểm tra UTF-16

### Bước 2: Ghi Chép Thông Tin
Tạo bảng ghi chép:
```
| Position | Type  | Length | Original Text | Translated Text |
|----------|-------|--------|---------------|----------------|
| 0x1234   | UTF-8 | 12     | Hello World   | Xin Chào       |
| 0x5678   | UTF-16| -12    | Menu          | Thực Đơn       |
```

## 4. Cách Import Text Đã Dịch

### 4.1 Chuẩn Bị Dữ Liệu Mới

**Cho UTF-8:**
1. Encode text mới thành UTF-8
2. Thêm null terminator (0x00)
3. Tính length mới = số bytes (bao gồm null terminator)

**Cho UTF-16:**
1. Encode text mới thành UTF-16LE
2. Thêm null terminator (0x00 0x00)
3. Tính số ký tự = (số bytes + 2) / 2
4. Length mới = -số_ký_tự

### 4.2 Thay Thế Dữ Liệu

**Bước 1: Backup File Gốc**
```
cp original.uasset backup.uasset
```

**Bước 2: Thay Thế Từng Entry**
1. Đi đến position của text entry
2. Xóa toàn bộ entry cũ (4 bytes length + text + terminator)
3. Chèn entry mới:
   - 4 bytes length mới (Little Endian)
   - Text data mới
   - Null terminator

**Ví dụ Thay Thế UTF-8:**
```
Text cũ: "Hello World" (12 bytes total)
Text mới: "Xin Chào" (9 bytes + 1 null = 10 bytes)

Dữ liệu cũ: 0C 00 00 00 48 65 6C 6C 6F 20 57 6F 72 6C 64 00
Dữ liệu mới: 0A 00 00 00 58 69 6E 20 43 68 C3 A0 6F 00
```

**Ví dụ Thay Thế UTF-16:**
```
Text cũ: "Menu" (-5 length, 10 bytes total)
Text mới: "Thực Đơn" (-9 length, 18 bytes total)

Dữ liệu cũ: FB FF FF FF 4D 00 65 00 6E 00 75 00 00 00
Dữ liệu mới: F7 FF FF FF 54 00 68 1B E1 00 63 00 20 00 44 01 A1 01 6E 00 00 00
```

### 4.3 Cập Nhật File Size

**Bước 1: Tính Size Change**
```
total_size_change = sum(new_entry_size - old_entry_size)
```

**Bước 2: Cập Nhật File Size**
1. Đi đến `size_offset_position`
2. Tính file size mới:
   ```
   new_file_size = old_file_size + total_size_change
   ```
3. Ghi đè 4 bytes tại vị trí đó với giá trị mới (Little Endian)

## 5. Công Thức Tính Toán Quan Trọng

### UTF-8 Length Calculation
```python
# Khi extract
actual_text_length = length - 1  # Trừ null terminator

# Khi import
new_length = len(utf8_bytes) + 1  # Cộng null terminator
```

### UTF-16 Length Calculation
```python
# Khi extract
actual_chars = -negative_length
byte_length = actual_chars * 2

# Khi import
new_chars = (len(utf16_bytes) + 2) // 2  # Bao gồm null terminator
new_length = -new_chars  # Âm cho UTF-16
```

### File Size Update
```python
# Tại size_offset_position
new_file_size = len(new_data) - size_offset_position + 96
```

## 6. Lưu Ý Quan Trọng

1. **Luôn backup file gốc** trước khi chỉnh sửa
2. **Kiểm tra encoding** của text trước khi thay thế
3. **Cập nhật file size** sau khi thay đổi tất cả text
4. **Test file** sau khi import để đảm bảo hoạt động
5. **Sử dụng Little Endian** cho tất cả integer values
6. **Đếm chính xác bytes** bao gồm null terminators

## 7. Troubleshooting

### File Không Load Được
- Kiểm tra file size có được cập nhật đúng không
- Kiểm tra null terminators có đầy đủ không
- Kiểm tra encoding của text mới

### Text Hiển Thị Sai
- Kiểm tra UTF-8/UTF-16 encoding
- Kiểm tra length calculation
- Kiểm tra Little Endian byte order

### Game Crash
- File size không đúng
- Cấu trúc dữ liệu bị hỏng
- Restore từ backup và thử lại