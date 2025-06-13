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
        
    def extract_texts(self, file_path: str) -> Dict:
        """Trích xuất text từ file .uasset"""
        try:
            with open(file_path, 'rb') as f:
                self.original_data = f.read()
            
            # Chuyển đổi sang string để tìm kiếm pattern
            data_str = self.original_data.decode('utf-8', errors='ignore')
            
            # Tìm các text entries
            text_data = self._parse_text_entries(data_str)
            
            return {
                'file_info': {
                    'original_file': file_path,
                    'file_size': len(self.original_data),
                    'total_entries': len(text_data)
                },
                'text_entries': text_data
            }
            
        except Exception as e:
            print(f"Lỗi khi đọc file: {e}")
            return {}
    
    def _parse_text_entries(self, data_str: str) -> List[Dict]:
        """Phân tích và trích xuất các text entries"""
        entries = []
        
        # Tìm các text có ý nghĩa (câu hoàn chỉnh, từ có nghĩa)
        # Pattern cho text có ý nghĩa: bắt đầu bằng chữ hoa, có khoảng trắng, dấu câu
        meaningful_patterns = [
            r'[A-Z][a-z]+(?:\s+[a-zA-Z]+)*[.!?]',  # Câu hoàn chỉnh
            r'[A-Z][a-z]+(?:\s+[a-zA-Z]+){2,}',     # Cụm từ dài
            r'[A-Z][a-z]+\s+[a-z]+\s*[?]',         # Câu hỏi
            r'[A-Z][a-z]+(?:\s+[a-z]+)*\s*[:]',    # Text có dấu hai chấm
        ]
        
        # Tìm tất cả text có ý nghĩa
        all_meaningful_texts = set()
        for pattern in meaningful_patterns:
            matches = re.findall(pattern, data_str)
            all_meaningful_texts.update(matches)
        
        # Tìm thêm các text dài có chứa từ thông dụng
        common_words = ['the', 'and', 'you', 'can', 'not', 'will', 'have', 'this', 'that', 'with', 'from', 'they', 'your', 'here', 'mode', 'name', 'enter', 'please']
        long_text_pattern = r'[A-Za-z][A-Za-z0-9\s\.,\?\!\-\(\)\[\]\{\}\'\"]{10,}'
        long_texts = re.findall(long_text_pattern, data_str)
        
        for text in long_texts:
            text = text.strip()
            # Kiểm tra xem có chứa từ thông dụng không
            text_lower = text.lower()
            if any(word in text_lower for word in common_words) and len(text) > 8:
                all_meaningful_texts.add(text)
        
        # Tìm các key/identifier
        key_pattern = r'\b([a-z]+_[a-z]+(?:_[a-z0-9]+)*)\b'
        keys = re.findall(key_pattern, data_str)
        
        # Tạo mapping key -> text
        current_key = None
        entry_id = 0
        processed_texts = set()  # Tránh trùng lặp
        
        # Sắp xếp theo vị trí xuất hiện trong file
        text_positions = []
        for text in all_meaningful_texts:
            pos = data_str.find(text)
            if pos != -1 and text not in processed_texts:
                text_positions.append((pos, text))
        
        text_positions.sort()  # Sắp xếp theo vị trí
        
        for pos, text in text_positions:
            if len(text.strip()) < 5:  # Bỏ qua text quá ngắn
                continue
                
            text = text.strip()
            
            # Tìm key gần nhất trước vị trí này
            best_key = None
            best_key_pos = -1
            for key in keys:
                key_pos = data_str.rfind(key, 0, pos)
                if key_pos > best_key_pos:
                    best_key_pos = key_pos
                    best_key = key
            
            # Tạo entry
            entry = {
                'id': entry_id,
                'key': best_key or f'text_entry_{entry_id}',
                'original_text': text,
                'translated_text': text,  # Mặc định giống original
                'language': self._detect_language(text),
                'position': pos,
                'length': len(text)
            }
            entries.append(entry)
            processed_texts.add(text)
            entry_id += 1
        
        # Lọc bỏ các entry trùng lặp hoặc không có ý nghĩa
        filtered_entries = []
        seen_texts = set()
        
        for entry in entries:
            text = entry['original_text']
            # Bỏ qua nếu:
            # - Text quá ngắn
            # - Chỉ chứa ký tự đặc biệt
            # - Đã thấy rồi
            if (len(text) < 5 or 
                re.match(r'^[^a-zA-Z]*$', text) or 
                text in seen_texts or
                text.count(' ') == 0 and len(text) < 10):  # Từ đơn quá ngắn
                continue
                
            seen_texts.add(text)
            filtered_entries.append(entry)
        
        return filtered_entries
    
    def _detect_language(self, text: str) -> str:
        """Phát hiện ngôn ngữ của text"""
        # Kiểm tra các ký tự đặc trung
        if re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', text.lower()):
            return 'vietnamese'
        elif re.search(r'[ひらがなカタカナ]', text):
            return 'japanese'
        elif re.search(r'[가-힣]', text):
            return 'korean'
        elif re.search(r'[一-龯]', text):
            return 'chinese'
        elif re.search(r'[àâäéèêëïîôöùûüÿç]', text.lower()):
            return 'french'
        elif re.search(r'[äöüß]', text.lower()):
            return 'german'
        elif re.search(r'[àèìòùáéíóú]', text.lower()):
            return 'italian'
        elif re.search(r'[ñáéíóúü]', text.lower()):
            return 'spanish'
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
    
    def rebuild_uasset(self, json_data: Dict, output_file: str):
        """Tái tạo file .uasset với text đã chỉnh sửa"""
        try:
            # Bắt đầu với dữ liệu gốc
            new_data = self.original_data
            
            # Thay thế từng text entry
            for entry in json_data.get('text_entries', []):
                original_text = entry['original_text']
                translated_text = entry['translated_text']
                
                if original_text != translated_text:
                    # Tìm và thay thế text trong binary data
                    original_bytes = original_text.encode('utf-8')
                    translated_bytes = translated_text.encode('utf-8')
                    
                    # Thay thế nếu tìm thấy
                    if original_bytes in new_data:
                        new_data = new_data.replace(original_bytes, translated_bytes, 1)
                        print(f"Đã thay thế: '{original_text}' -> '{translated_text}'")
            
            # Ghi file mới
            with open(output_file, 'wb') as f:
                f.write(new_data)
            
            print(f"Đã tạo file mới: {output_file}")
            
        except Exception as e:
            print(f"Lỗi khi tái tạo file .uasset: {e}")

def batch_extract_all():
    """Trích xuất tất cả file .uasset trong folder hiện tại và folder 'original' ra folder 'extract'"""
    extractor = UAssetTextExtractor()
    
    # Tạo folder extract nếu chưa có
    extract_folder = "extract"
    if not os.path.exists(extract_folder):
        os.makedirs(extract_folder)
        print(f"Đã tạo folder: {extract_folder}")
    
    # Tìm tất cả file .uasset trong folder hiện tại
    uasset_files = [f for f in os.listdir('.') if f.endswith('.uasset')]
    
    # Tìm thêm file .uasset trong folder "original" nếu có
    original_folder = "original"
    if os.path.exists(original_folder):
        original_files = [os.path.join(original_folder, f) for f in os.listdir(original_folder) if f.endswith('.uasset')]
        uasset_files.extend(original_files)
        print(f"Tìm thấy thêm {len(original_files)} file trong folder original")
    
    if not uasset_files:
        print("Không tìm thấy file .uasset nào trong folder hiện tại và folder original")
        return
    
    print(f"Tìm thấy {len(uasset_files)} file .uasset:")
    for file in uasset_files:
        print(f"  - {file}")
    
    print("\nBắt đầu trích xuất...")
    
    success_count = 0
    for uasset_file in uasset_files:
        try:
            print(f"\n📁 Đang xử lý: {uasset_file}")
            
            # Trích xuất text
            extracted_data = extractor.extract_texts(uasset_file)
            
            if extracted_data and extracted_data.get('text_entries'):
                # Tạo tên file JSON trong folder extract
                json_filename = uasset_file.replace('.uasset', '_texts.json')
                json_path = os.path.join(extract_folder, json_filename)
                
                # Xuất ra file JSON
                extractor.export_to_json(extracted_data, json_path)
                
                entry_count = len(extracted_data.get('text_entries', []))
                print(f"  ✅ Thành công: {entry_count} text entries -> {json_path}")
                success_count += 1
            else:
                print(f"  ⚠️  Không tìm thấy text có ý nghĩa trong {uasset_file}")
                
        except Exception as e:
            print(f"  ❌ Lỗi khi xử lý {uasset_file}: {e}")
    
    print(f"\n🎉 Hoàn thành! Đã trích xuất thành công {success_count}/{len(uasset_files)} file")
    print(f"📂 Các file JSON đã được lưu trong folder: {extract_folder}")

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
            new_filename = original_filename.replace('.uasset', '_translated.uasset')
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