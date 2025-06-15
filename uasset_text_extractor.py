#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UAsset Text Extractor and Importer
Trích xuất và import lại text từ file .uasset của Unreal Engine
"""

import re
import json
import struct
from typing import Dict, List, Tuple, Optional
import argparse
import os

class UAssetTextExtractor:
    def __init__(self):
        self.text_entries = []
        self.original_data = b''
        self.original_file_size = 0
        self.size_offset_position = 0
        
    def extract_texts(self, file_path: str) -> Dict:
        """Trích xuất text từ file .uasset"""
        try:
            print(f"📂 Đang đọc file: {file_path}")
            with open(file_path, 'rb') as f:
                self.original_data = f.read()
            
            file_size_mb = len(self.original_data) / (1024 * 1024)
            print(f"📊 Kích thước file: {file_size_mb:.2f} MB ({len(self.original_data):,} bytes)")
            
            print("🔄 Đang chuyển đổi dữ liệu binary sang text...")
            # Chuyển đổi sang string để tìm kiếm pattern
            data_str = self.original_data.decode('utf-8', errors='ignore')
            print(f"📝 Độ dài text sau chuyển đổi: {len(data_str):,} ký tự")
            
            print("🚀 Bắt đầu phân tích và trích xuất text...")
            # Tìm các text entries
            text_data = self._parse_text_entries(data_str)
            
            # Đọc thông tin kích thước file từ offset 0x20
            size_info = self._read_file_size_info()
            
            result = {
                'file_info': {
                    'original_file': file_path,
                    'file_size': len(self.original_data),
                    'total_entries': len(text_data),
                    'original_file_size': self.original_file_size,
                    'size_offset_position': self.size_offset_position
                },
                'text_entries': text_data
            }
            
            print(f"🎉 Trích xuất hoàn tất! Tìm thấy {len(text_data)} text entries")
            return result
            
        except Exception as e:
            print(f"❌ Lỗi khi đọc file: {e}")
            return {}
    
    def _parse_text_entries(self, data_str: str) -> List[Dict]:
        """Phân tích và trích xuất các text entries dựa trên cấu trúc file uasset."""
        entries = []
        entry_id = 0
        processed_texts = set() # Để tránh trùng lặp
        original_binary_data = self.original_data
        data_len = len(original_binary_data)
        idx = 0

        print("🚀 Bắt đầu phân tích file binary...")

        while idx < data_len - 4: # Cần ít nhất 4 byte cho độ dài
            try:
                # Thử đọc UTF-8 string: <u32 len><string + 1>
                # Độ dài được lưu là little-endian integer
                str_len = struct.unpack('<i', original_binary_data[idx:idx+4])[0]
                
                # Kiểm tra độ dài hợp lệ và có null terminator
                # Độ dài của chuỗi text thực tế (không bao gồm null terminator)
                actual_str_len = str_len -1

                if 0 < actual_str_len < 200: # Giới hạn độ dài hợp lý, tránh đọc sai dữ liệu
                    if idx + 4 + str_len <= data_len:
                        # Kiểm tra null terminator cho UTF-8
                        if original_binary_data[idx + 4 + actual_str_len] == 0:
                            text_bytes = original_binary_data[idx+4 : idx+4+actual_str_len]
                            try:
                                text = text_bytes.decode('utf-8')
                                # Lọc các chuỗi không phải text (ví dụ: toàn ký tự đặc biệt, hoặc quá ngắn)
                                if re.search(r'[a-zA-Z0-9]', text) and len(text.strip()) > 3 and text not in processed_texts:
                                    if not any(c in text for c in ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0b', '\x0c', '\x0e', '\x0f']): # Loại bỏ các ký tự control không mong muốn
                                        entries.append({
                                            'id': entry_id,
                                            'key': f'utf8_entry_{entry_id}',
                                            'original_text': text.strip(),
                                            'translated_text': text.strip(),
                                            'language': self._detect_language(text),
                                            'position': idx,
                                            'length': str_len
                                        })
                                        processed_texts.add(text)
                                        entry_id += 1
                                        # print(f"Found UTF-8: {text.strip()} at {idx}")
                                        idx += 4 + str_len # Di chuyển con trỏ qua độ dài + chuỗi + null terminator
                                        continue
                            except UnicodeDecodeError:
                                pass # Không phải UTF-8 hợp lệ
                
                # Thử đọc UTF-16 string: <u32 len^0xFF><(string + 1)/2>
                # Độ dài được lưu là little-endian integer, XOR với 0xFFFFFFFF (hoặc -len nếu là số âm)
                # Unreal Engine lưu độ dài âm cho UTF-16
                str_len_utf16_encoded = struct.unpack('<i', original_binary_data[idx:idx+4])[0]
                
                if str_len_utf16_encoded < 0: # Độ dài âm là dấu hiệu của UTF-16
                    actual_num_chars = -str_len_utf16_encoded
                    byte_len_utf16 = actual_num_chars * 2 # Mỗi ký tự UTF-16 là 2 bytes

                    if 0 < actual_num_chars < 200: # Giới hạn độ dài hợp lý
                        if idx + 4 + byte_len_utf16 <= data_len:
                             # Kiểm tra null terminator cho UTF-16 (2 bytes 00 00)
                            if original_binary_data[idx + 4 + byte_len_utf16 - 2 : idx + 4 + byte_len_utf16] == b'\x00\x00':
                                text_bytes = original_binary_data[idx+4 : idx+4+byte_len_utf16-2] # Bỏ qua 2 byte null terminator
                                try:
                                    text = text_bytes.decode('utf-16-le')
                                    if re.search(r'[a-zA-Z0-9]', text) and len(text.strip()) > 3 and text not in processed_texts:
                                        if not any(c in text for c in ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07', '\x08', '\x0b', '\x0c', '\x0e', '\x0f']): # Loại bỏ các ký tự control không mong muốn
                                            entries.append({
                                                'id': entry_id,
                                                'key': f'utf16_entry_{entry_id}',
                                                'original_text': text.strip(),
                                                'translated_text': text.strip(),
                                                'language': self._detect_language(text),
                                                'position': idx,
                                                'length': byte_len_utf16
                                            })
                                            processed_texts.add(text)
                                            entry_id += 1
                                            # print(f"Found UTF-16: {text.strip()} at {idx}")
                                            idx += 4 + byte_len_utf16 # Di chuyển con trỏ
                                            continue
                                except UnicodeDecodeError:
                                    pass # Không phải UTF-16 hợp lệ

            except struct.error:
                # Không thể unpack 4 bytes, có thể đã đến cuối file hoặc dữ liệu không hợp lệ
                pass
            except Exception as e:
                # print(f"Error parsing at {idx}: {e}")
                pass # Bỏ qua lỗi và tiếp tục

            idx += 1 # Di chuyển con trỏ một byte nếu không tìm thấy gì

        print(f"🎉 Phân tích binary hoàn tất! Tìm thấy {len(entries)} text entries.")
        
        # Lọc và sắp xếp lại nếu cần, hiện tại đã lọc trong vòng lặp
        # Sắp xếp theo vị trí để đảm bảo thứ tự
        entries.sort(key=lambda e: e['position'])
        # Cập nhật lại ID sau khi sắp xếp
        for i, entry in enumerate(entries):
            entry['id'] = i
            entry['key'] = f"{entry['key'].split('_')[0]}_entry_{i}" # Cập nhật key với id mới

        return entries
    
    def _detect_language(self, text: str) -> str:
        """Phát hiện ngôn ngữ của text"""
        text_lower = text.lower()
        words = text_lower.split()
        
        # Kiểm tra các ký tự đặc trưng theo thứ tự ưu tiên
     
        
        # 2. Tiếng Nhật
        if re.search(r'[ひらがなカタカナ]', text):
            return 'japanese'
        
        # 3. Tiếng Hàn
        elif re.search(r'[가-힣]', text):
            return 'korean'
        
        # 4. Tiếng Trung
        elif re.search(r'[一-龯]', text):
            return 'chinese'
        
        # 5. Tiếng Đức (kiểm tra ký tự đặc biệt)
        elif re.search(r'[äöüß]', text_lower):
            return 'german'
        
        # 6. Kiểm tra từ khóa đặc trưng riêng biệt
        # Đếm số từ khóa của mỗi ngôn ngữ
        german_words = ['der', 'die', 'das', 'und', 'ist', 'nicht', 'ein', 'eine', 'zu', 'auf', 'mit', 'sich', 'auch', 'noch', 'alle', 'sein', 'werden', 'haben', 'können', 'müssen', 'sollen', 'wollen', 'scheinen', 'jedoch']
        french_words = ['le', 'la', 'les', 'du', 'des', 'et', 'est', 'une', 'dans', 'pour', 'que', 'qui', 'avec', 'sur', 'par', 'tout', 'tous', 'cette', 'ces', 'mais', 'pas', 'très', 'être', 'avoir', 'faire', 'aller', 'voir', 'savoir', 'pouvoir', 'vouloir', 'devoir']
        italian_words = ['il', 'lo', 'gli', 'della', 'dello', 'degli', 'delle', 'con', 'per', 'tra', 'fra', 'che', 'non', 'una', 'uno', 'questo', 'questa', 'quello', 'quella', 'essere', 'avere', 'fare', 'dire', 'andare', 'potere', 'dovere', 'volere', 'sapere', 'dare', 'ciao', 'mondo', 'come', 'dove', 'quando', 'perché', 'molto', 'bene', 'male', 'grande', 'piccolo']
        spanish_words = ['el', 'los', 'las', 'del', 'por', 'para', 'no', 'este', 'esta', 'ese', 'esa', 'aquel', 'aquella', 'ser', 'estar', 'tener', 'hacer', 'decir', 'ir', 'poder', 'deber', 'querer', 'saber', 'dar', 'hola', 'mundo', 'como', 'donde', 'cuando', 'porque', 'muy', 'bien', 'mal', 'grande', 'pequeño']
        english_words = ['the', 'and', 'you', 'that', 'what', 'with', 'have', 'this', 'will', 'your', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were', 'buddy', 'found', 'heard', 'water', 'hit', 'lets']
        
        # Đếm từ khóa cho mỗi ngôn ngữ
        german_count = sum(1 for word in words if word in german_words)
        french_count = sum(1 for word in words if word in french_words)
        italian_count = sum(1 for word in words if word in italian_words)
        spanish_count = sum(1 for word in words if word in spanish_words)
        english_count = sum(1 for word in words if word in english_words)
        
        # Tìm ngôn ngữ có nhiều từ khóa nhất
        language_scores = {
            'german': german_count,
            'french': french_count,
            'italian': italian_count,
        'spanish': spanish_count,
            'english': english_count
        }
        
        # Nếu có từ khóa được tìm thấy, trả về ngôn ngữ có điểm cao nhất
        max_score = max(language_scores.values())
        if max_score > 0:
            for lang, score in language_scores.items():
                if score == max_score:
                    return lang
        
        # 7. Kiểm tra ký tự có dấu cho các ngôn ngữ châu Âu (fallback)
        elif re.search(r'[àâäéèêëïîôöùûüÿç]', text_lower):
            return 'french'
        elif re.search(r'[àèìòùáéíóú]', text_lower):
            return 'italian'
        elif re.search(r'[ñáéíóúü]', text_lower):
            return 'spanish'
        
        # 8. Mặc định là tiếng Anh
        else:
            return 'english'
    
    def export_to_json(self, extracted_data: Dict, output_file: str):
        """Xuất dữ liệu ra file JSON để chỉnh sửa"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extracted_data, f, ensure_ascii=False, indent=2)
            print(f"Đã xuất dữ liệu ra: {output_file}")
        except Exception as e:
            print(f"Lỗi khi xuất file JSON: {e}")
    
    def import_from_json(self, json_file: str) -> Dict:
        """Đọc dữ liệu đã chỉnh sửa từ file JSON"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Lỗi khi đọc file JSON: {e}")
            return {}
    
    def _read_file_size_info(self):
        """Đọc thông tin kích thước file từ offset 0x20"""
        try:
            if len(self.original_data) >= 0x24:  # Cần ít nhất 0x24 bytes
                # Đọc 4 bytes tại offset 0x20 để lấy offset của vị trí lưu kích thước
                self.size_offset_position = struct.unpack('<I', self.original_data[0x20:0x24])[0]
                print(f"📍 Size offset position: {self.size_offset_position} (0x{self.size_offset_position:X})")
                
                if self.size_offset_position > 0 and self.size_offset_position < len(self.original_data):
                    # Tính kích thước từ size_offset_position đến cuối file, trừ thêm 104
                    self.original_file_size = len(self.original_data) - self.size_offset_position - 104
                    print(f"📏 Original file size: {self.original_file_size} bytes (tính từ offset 0x{self.size_offset_position:X} đến cuối file, trừ 104)")
                    print(f"📏 Công thức: {len(self.original_data)} - {self.size_offset_position} - 104 = {self.original_file_size}")
                    return True
                else:
                    print(f"⚠️ Size offset position không hợp lệ: {self.size_offset_position} (file size: {len(self.original_data)})")
        except Exception as e:
            print(f"⚠️ Không thể đọc thông tin kích thước file: {e}")
            self.original_file_size = len(self.original_data)
            self.size_offset_position = 0
        return False
    
    def _insert_data_at_position(self, data: bytearray, position: int, new_data: bytes, old_length: int) -> tuple[bytearray, int]:
        """Thay thế dữ liệu tại vị trí cụ thể với dynamic resizing
        Returns: (updated_data, size_change)
        """
        try:
            new_length = len(new_data)
            size_change = new_length - old_length
            
            print(f"🔄 Thay thế tại 0x{position:X}: {old_length} -> {new_length} bytes (thay đổi: {size_change:+d})")
            
            # Bước 1: Xóa toàn bộ vùng cũ
            del data[position:position + old_length]
            print(f"🗑️ Đã xóa {old_length} bytes tại vị trí 0x{position:X}")
            
            # Bước 2: Chèn dữ liệu mới vào vị trí đó
            data[position:position] = new_data
            print(f"✏️ Đã chèn {new_length} bytes tại vị trí 0x{position:X}")
            
            return data, size_change
            
        except Exception as e:
            print(f"❌ Lỗi khi thay thế dữ liệu: {e}")
            import traceback
            traceback.print_exc()
            return data, 0
    
    def _calculate_new_file_size(self, new_data: bytearray, size_offset_position: int = None) -> int:
        """Tính toán kích thước file mới từ size_offset_position đến cuối file, trừ thêm 104"""
        try:
            if size_offset_position is not None and size_offset_position > 0:
                # Tính từ size_offset_position đến cuối file, trừ thêm 104
                new_size = len(new_data) - size_offset_position - 104
                print(f"📐 Tính toán kích thước mới từ offset 0x{size_offset_position:X}: {len(new_data)} - {size_offset_position} - 104 = {new_size}")
                return new_size
            else:
                # Fallback: tính theo cách cũ
                # Kiểm tra 4 byte cuối có phải là C1 83 2A 9E không
                if len(new_data) >= 4:
                    last_4_bytes = new_data[-4:]
                    expected_bytes = bytes([0xC1, 0x83, 0x2A, 0x9E])
                    
                    if last_4_bytes == expected_bytes:
                        new_size = len(new_data) - 4 - 100
                        print(f"📐 Tính toán kích thước mới (fallback): {len(new_data)} - 4 - 100 = {new_size}")
                        return new_size
                    else:
                        print(f"⚠️ 4 byte cuối không phải C1 83 2A 9E: {last_4_bytes.hex().upper()}")
                
                # Fallback cuối cùng: chỉ trừ 100
                new_size = len(new_data) - 100
                print(f"📐 Tính toán kích thước mới (fallback): {len(new_data)} - 100 = {new_size}")
                return new_size
            
        except Exception as e:
            print(f"❌ Lỗi khi tính toán kích thước mới: {e}")
            return len(new_data)

    def rebuild_uasset(self, json_data: Dict, output_file: str):
        """Tái tạo file .uasset với text đã chỉnh sửa, cập nhật đúng len và size tổng cho UTF-8/UTF-16 với dynamic resizing"""
        try:
            # Bắt đầu với dữ liệu gốc
            new_data = bytearray(self.original_data)
            
            # Lấy thông tin kích thước từ JSON nếu có
            file_info = json_data.get('file_info', {})
            original_file_size = file_info.get('original_file_size', self.original_file_size)
            size_offset_position = file_info.get('size_offset_position', self.size_offset_position)
            
            # Theo dõi tổng thay đổi kích thước để cập nhật các offset sau
            total_size_change = 0
            processed_entries = []
            
            # Sắp xếp entries theo position để xử lý từ cuối lên đầu (tránh ảnh hưởng offset)
            sorted_entries = sorted(json_data.get('text_entries', []), key=lambda x: x['position'], reverse=True)
            
            for entry in sorted_entries:
                original_text = entry['original_text']
                translated_text = entry['translated_text']
                position = entry['position']
                length = entry['length']
                key = entry['key']
                
                if original_text == translated_text:
                    continue
                    
                print(f"\n🔄 Xử lý entry tại 0x{position:X}: '{original_text}' -> '{translated_text}'")
                
                if key.startswith('utf8_entry'):
                    # <u32 len><string + 1>
                    new_bytes = translated_text.encode('utf-8') + b'\x00'
                    new_len = len(new_bytes)
                    # length đã bao gồm cả null terminator, vậy old_text_length = length
                    old_text_length = length
                    
                    # Cập nhật length field
                    new_data[position:position+4] = struct.pack('<i', new_len)
                    
                    # Sử dụng dynamic resizing cho text data
                    new_data, size_change = self._insert_data_at_position(
                        new_data, position + 4, new_bytes, old_text_length
                    )
                    total_size_change += size_change
                    
                elif key.startswith('utf16_entry'):
                    # <u32 len^0xFF><(string + 1)/2>
                    new_bytes = translated_text.encode('utf-16-le') + b'\x00\x00'
                    new_len = len(new_bytes) // 2
                    # length đã bao gồm cả null terminator, vậy old_text_length = length
                    old_text_length = length
                    
                    # Cập nhật length field (âm, little-endian)
                    new_data[position:position+4] = struct.pack('<i', -new_len)
                    
                    # Sử dụng dynamic resizing cho text data
                    new_data, size_change = self._insert_data_at_position(
                        new_data, position + 4, new_bytes, old_text_length
                    )
                    total_size_change += size_change
                
                processed_entries.append({
                    'position': position,
                    'old_text': original_text,
                    'new_text': translated_text,
                    'size_change': size_change if 'size_change' in locals() else 0
                })
            
            print(f"\n📊 Tổng kết thay đổi kích thước: {total_size_change} bytes")
            print(f"📏 Kích thước file: {len(self.original_data)} -> {len(new_data)} bytes")
            
            # Cập nhật kích thước file mới với dynamic sizing
            if size_offset_position > 0:
                # Tính vị trí thực tế để ghi kích thước (offset + 8)
                actual_size_position = size_offset_position + 8
                if actual_size_position + 4 <= len(new_data):
                    # Tính vị trí bắt đầu tính toán kích thước (actual_size_position + 4)
                    start_calc_position = actual_size_position + 4
                    new_file_size = self._calculate_new_file_size(new_data, start_calc_position)
                    new_data[actual_size_position:actual_size_position+4] = struct.pack('<I', new_file_size)
                    print(f"📝 Đã cập nhật kích thước file tại offset 0x{actual_size_position:X} (0x{size_offset_position:X} + 8): {original_file_size} -> {new_file_size}")
                    print(f"📏 Tính kích thước từ vị trí: 0x{start_calc_position:X}")
                    print(f"🔄 Thay đổi tổng cộng: {total_size_change} bytes")
                else:
                    print(f"⚠️ Vị trí ghi kích thước không hợp lệ: 0x{actual_size_position:X} vượt quá kích thước file")
            
            # Ghi file output với kích thước mới
            with open(output_file, 'wb') as f:
                f.write(new_data)
            
            print(f"\n✅ Đã tạo file mới: {output_file}")
            print(f"📈 Kích thước thay đổi: {len(self.original_data)} -> {len(new_data)} bytes ({total_size_change:+d})")
            
            # Hiển thị thống kê chi tiết
            if processed_entries:
                print(f"\n📋 Chi tiết {len(processed_entries)} entries đã xử lý:")
                for i, entry in enumerate(processed_entries[:5], 1):  # Chỉ hiển thị 5 entries đầu
                    print(f"  {i}. 0x{entry['position']:X}: '{entry['old_text'][:20]}...' -> '{entry['new_text'][:20]}...' ({entry['size_change']:+d} bytes)")
                if len(processed_entries) > 5:
                    print(f"  ... và {len(processed_entries) - 5} entries khác")
                    
        except Exception as e:
            print(f"❌ Lỗi khi tái tạo file .uasset: {e}")
            import traceback
            traceback.print_exc()

def batch_extract_all():
    """Trích xuất tất cả file .uasset trong folder hiện tại và folder 'original' ra folder 'extract'"""
    import time
    
    extractor = UAssetTextExtractor()
    
    # Tạo folder extract nếu chưa có
    extract_folder = "extract"
    if not os.path.exists(extract_folder):
        os.makedirs(extract_folder)
        print(f"📁 Đã tạo folder: {extract_folder}")
    
    # Tìm tất cả file .uasset trong folder hiện tại
    uasset_files = [f for f in os.listdir('.') if f.endswith('.uasset')]
    
    # Tìm thêm file .uasset trong folder "original" nếu có
    original_folder = "original"
    if os.path.exists(original_folder):
        original_files = [os.path.join(original_folder, f) for f in os.listdir(original_folder) if f.endswith('.uasset')]
        uasset_files.extend(original_files)
        print(f"📁 Tìm thấy thêm {len(original_files)} file trong folder original")
    
    if not uasset_files:
        print("❌ Không tìm thấy file .uasset nào trong folder hiện tại và folder original")
        return
    
    print(f"\n📋 Danh sách {len(uasset_files)} file .uasset sẽ được xử lý:")
    for i, file in enumerate(uasset_files, 1):
        file_size = os.path.getsize(file) / (1024 * 1024) if os.path.exists(file) else 0
        print(f"  {i:2d}. {file} ({file_size:.2f} MB)")
    
    print(f"\n🚀 Bắt đầu trích xuất {len(uasset_files)} file...")
    print("=" * 60)
    
    start_time = time.time()
    success_count = 0
    total_entries = 0
    
    for i, uasset_file in enumerate(uasset_files, 1):
        try:
            file_start_time = time.time()
            print(f"\n📁 [{i}/{len(uasset_files)}] Đang xử lý: {uasset_file}")
            
            # Trích xuất text
            extracted_data = extractor.extract_texts(uasset_file)
            
            if extracted_data and extracted_data.get('text_entries'):
                # Tạo tên file JSON trong folder extract
                json_filename = os.path.basename(uasset_file).replace('.uasset', '_texts.json')
                json_path = os.path.join(extract_folder, json_filename)
                
                # Xuất ra file JSON
                extractor.export_to_json(extracted_data, json_path)
                
                entry_count = len(extracted_data.get('text_entries', []))
                total_entries += entry_count
                file_time = time.time() - file_start_time
                
                print(f"  ✅ Thành công: {entry_count} text entries -> {json_path}")
                print(f"  ⏱️  Thời gian xử lý: {file_time:.2f}s")
                success_count += 1
            else:
                print(f"  ⚠️  Không tìm thấy text có ý nghĩa trong {uasset_file}")
            
            # Tính toán thời gian ước tính còn lại
            elapsed_time = time.time() - start_time
            if i > 0:
                avg_time_per_file = elapsed_time / i
                remaining_files = len(uasset_files) - i
                estimated_remaining = avg_time_per_file * remaining_files
                print(f"  📊 Tiến trình: {i}/{len(uasset_files)} ({i/len(uasset_files)*100:.1f}%)")
                print(f"  ⏰ Thời gian ước tính còn lại: {estimated_remaining/60:.1f} phút")
                
        except Exception as e:
            print(f"  ❌ Lỗi khi xử lý {uasset_file}: {e}")
            import traceback
            print(f"  🔍 Chi tiết lỗi: {traceback.format_exc()}")
    
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print(f"🎉 HOÀN THÀNH! Kết quả tổng kết:")
    print(f"  ✅ Thành công: {success_count}/{len(uasset_files)} file")
    print(f"  📝 Tổng text entries: {total_entries:,}")
    print(f"  ⏱️  Tổng thời gian: {total_time/60:.2f} phút")
    print(f"  📂 Các file JSON đã được lưu trong folder: {extract_folder}")
    
    if success_count < len(uasset_files):
        failed_count = len(uasset_files) - success_count
        print(f"  ⚠️  {failed_count} file không thể xử lý - kiểm tra log ở trên để biết chi tiết")

def batch_import_all():
    """Import tất cả file JSON từ folder 'extract' và tạo file .uasset mới trong folder 'import'"""
    extractor = UAssetTextExtractor()
    
    extract_folder = "extract"
    import_folder = "import"
    
    # Kiểm tra folder extract
    if not os.path.exists(extract_folder):
        print(f"Không tìm thấy folder: {extract_folder}")
        print("Hãy chạy 'batch-extract' trước")
        return
    
    # Tạo folder import nếu chưa có
    if not os.path.exists(import_folder):
        os.makedirs(import_folder)
        print(f"Đã tạo folder: {import_folder}")
    
    # Tìm tất cả file JSON trong folder extract
    json_files = [f for f in os.listdir(extract_folder) if f.endswith('_texts.json')]
    
    if not json_files:
        print(f"Không tìm thấy file JSON nào trong folder: {extract_folder}")
        return
    
    print(f"Tìm thấy {len(json_files)} file JSON:")
    for file in json_files:
        print(f"  - {file}")
    
    print("\nBắt đầu import...")
    
    success_count = 0
    for json_file in json_files:
        try:
            json_path = os.path.join(extract_folder, json_file)
            print(f"\n📁 Đang xử lý: {json_file}")
            
            # Đọc file JSON
            json_data = extractor.import_from_json(json_path)
            if not json_data:
                print(f"  ❌ Không thể đọc file JSON: {json_file}")
                continue
            
            # Tìm file .uasset gốc
            original_uasset = json_data.get('file_info', {}).get('original_file')
            if not original_uasset or not os.path.exists(original_uasset):
                print(f"  ❌ Không tìm thấy file .uasset gốc cho {json_file}")
                continue
            
            # Đọc lại file gốc
            extractor.extract_texts(original_uasset)
            
            # Tạo tên file .uasset mới trong folder import
            original_filename = os.path.basename(original_uasset)
            new_filename = original_filename.replace('.uasset', '.uasset')
            new_path = os.path.join(import_folder, new_filename)
            
            # Tạo file .uasset mới
            extractor.rebuild_uasset(json_data, new_path)
            
            print(f"  ✅ Thành công: {new_path}")
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ Lỗi khi xử lý {json_file}: {e}")
    
    print(f"\n🎉 Hoàn thành! Đã import thành công {success_count}/{len(json_files)} file")
    print(f"📂 Các file .uasset mới đã được lưu trong folder: {import_folder}")

def main():
    parser = argparse.ArgumentParser(description='UAsset Text Extractor and Importer')
    parser.add_argument('action', choices=['extract', 'import', 'batch-extract', 'batch-import'], 
                       help='Hành động: extract, import, batch-extract, batch-import')
    parser.add_argument('input_file', nargs='?', help='File đầu vào (.uasset hoặc .json) - không cần cho batch operations')
    parser.add_argument('-o', '--output', help='File đầu ra')
    
    args = parser.parse_args()
    
    extractor = UAssetTextExtractor()
    
    if args.action == 'batch-extract':
        # Trích xuất tất cả file .uasset trong folder hiện tại
        batch_extract_all()
        
    elif args.action == 'batch-import':
        # Import tất cả file từ folder extract
        batch_import_all()
        
    elif args.action == 'extract':
        # Trích xuất text từ .uasset
        if not args.input_file:
            print("Cần chỉ định file đầu vào cho action 'extract'")
            return
            
        if not args.input_file.endswith('.uasset'):
            print("File đầu vào phải là .uasset")
            return
        
        output_file = args.output or args.input_file.replace('.uasset', '_texts.json')
        
        print(f"Đang trích xuất text từ: {args.input_file}")
        extracted_data = extractor.extract_texts(args.input_file)
        
        if extracted_data:
            extractor.export_to_json(extracted_data, output_file)
            print(f"Tìm thấy {len(extracted_data.get('text_entries', []))} text entries")
        else:
            print("Không thể trích xuất dữ liệu")
    
    elif args.action == 'import':
        # Import text đã chỉnh sửa và tạo .uasset mới
        if not args.input_file:
            print("Cần chỉ định file đầu vào cho action 'import'")
            return
            
        if not args.input_file.endswith('.json'):
            print("File đầu vào phải là .json")
            return
        
        json_data = extractor.import_from_json(args.input_file)
        if not json_data:
            print("Không thể đọc file JSON")
            return
        
        original_uasset = json_data.get('file_info', {}).get('original_file')
        if not original_uasset or not os.path.exists(original_uasset):
            print("Không tìm thấy file .uasset gốc")
            return
        
        # Đọc lại file gốc
        extractor.extract_texts(original_uasset)
        
        output_file = args.output or original_uasset.replace('.uasset', '_translated.uasset')
        
        print(f"Đang tạo file .uasset mới từ: {args.input_file}")
        extractor.rebuild_uasset(json_data, output_file)

if __name__ == '__main__':
    # Ví dụ sử dụng nếu chạy trực tiếp
    if len(os.sys.argv) == 1:
        print("Ví dụ sử dụng:")
        print("1. Trích xuất text: python uasset_text_extractor.py extract GDSSystemText.uasset")
        print("2. Import text: python uasset_text_extractor.py import GDSSystemText_texts.json")
        print("")
        
        # Demo với file hiện tại
        extractor = UAssetTextExtractor()
        demo_file = "/Users/phamminhkha/Desktop/DichGame/GDSSystemText.uasset"
        
        if os.path.exists(demo_file):
            print(f"Demo: Trích xuất text từ {demo_file}")
            extracted_data = extractor.extract_texts(demo_file)
            
            if extracted_data:
                output_json = demo_file.replace('.uasset', '_texts.json')
                extractor.export_to_json(extracted_data, output_json)
                print(f"Đã tạo file: {output_json}")
                print(f"Tìm thấy {len(extracted_data.get('text_entries', []))} text entries")
                
                # Hiển thị một vài ví dụ
                print("\nMột vài text entries đầu tiên:")
                for i, entry in enumerate(extracted_data.get('text_entries', [])[:5]):
                    print(f"{i+1}. [{entry['language']}] {entry['original_text'][:50]}...")
    else:
        main()