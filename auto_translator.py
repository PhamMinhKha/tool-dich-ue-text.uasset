#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto Translator using Google Gemini API
Tự động dịch các file JSON đã extract sang tiếng Việt
"""

import os
import json
import time
import argparse
from typing import Dict, List, Optional
import google.generativeai as genai
from datetime import datetime

class AutoTranslator:
    def __init__(self, api_key: str = None):
        """
        Khởi tạo Auto Translator
        
        Args:
            api_key: Google Gemini API key. Nếu không có, sẽ đọc từ listkey.txt hoặc biến môi trường
        """
        # Load danh sách API keys
        self.api_keys = self.load_api_keys()
        self.current_key_index = 0
        
        # Nếu có api_key truyền vào, ưu tiên sử dụng
        if api_key:
            self.api_keys.insert(0, api_key)
        
        if not self.api_keys:
            raise ValueError("Cần có API key. Thêm vào file listkey.txt hoặc đặt biến môi trường GEMINI_API_KEY")
        
        # Cấu hình Gemini với key đầu tiên
        self.setup_gemini_model()
        
        # Cache và từ điển
        self.cache_file = "translation_cache.json"
        self.dictionary_file = "tudien.json"
        self.cache = self.load_cache()
        self.dictionary = self.load_dictionary()
        
        # Thống kê
        self.stats = {
            'total': 0,
            'translated': 0,
            'cached': 0,
            'dictionary': 0,
            'skipped': 0
        }
        
    def load_api_keys(self) -> List[str]:
        """Load danh sách API keys từ file listkey.txt và biến môi trường"""
        keys = []
        
        # Đọc từ file listkey.txt
        if os.path.exists("listkey.txt"):
            try:
                with open("listkey.txt", 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        # Bỏ qua dòng comment và dòng trống
                        if line and not line.startswith('#'):
                            keys.append(line)
            except Exception as e:
                print(f"⚠️  Không thể đọc listkey.txt: {e}")
        
        # Thêm từ biến môi trường nếu có
        env_key = os.getenv('GEMINI_API_KEY')
        if env_key and env_key not in keys:
            keys.append(env_key)
            
        return keys
    
    def setup_gemini_model(self):
        """Cấu hình Gemini model với API key hiện tại"""
        current_key = self.api_keys[self.current_key_index]
        genai.configure(api_key=current_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        print(f"🔑 Sử dụng API key #{self.current_key_index + 1}/{len(self.api_keys)}")
    
    def switch_to_next_key(self) -> bool:
        """Chuyển sang API key tiếp theo. Trả về True nếu còn key khả dụng, False nếu đã hết danh sách"""
        self.current_key_index += 1
        if self.current_key_index < len(self.api_keys):
            self.setup_gemini_model()
            return True
        return False
    
    def reset_to_first_key(self):
        """Reset về key đầu tiên để bắt đầu vòng mới"""
        self.current_key_index = 0
        self.setup_gemini_model()
    
    def load_cache(self) -> Dict[str, str]:
        """Tải cache từ file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Lỗi khi đọc cache: {e}")
        return {}
    
    def save_cache(self):
        """Lưu cache ra file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Lỗi khi lưu cache: {e}")
    
    def load_dictionary(self) -> Dict[str, str]:
        """Tải từ điển từ file tudien.json"""
        if os.path.exists(self.dictionary_file):
            try:
                with open(self.dictionary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Chuyển tất cả key thành chữ thường để so sánh
                    return {k.lower(): v for k, v in data.items()}
            except Exception as e:
                print(f"⚠️  Lỗi khi đọc từ điển: {e}")
        return {}
    
    def get_translation_from_dictionary(self, text: str) -> Optional[str]:
        """Kiểm tra xem text có trong từ điển không"""
        text_lower = text.lower().strip()
        return self.dictionary.get(text_lower)
    
    def get_translation_from_cache(self, text: str) -> Optional[str]:
        """Lấy bản dịch từ cache"""
        return self.cache.get(text)
    

    def translate_with_gemini(self, text: str) -> str:
        """Dịch text bằng Google Gemini với bối cảnh game và multiple API keys (xoay vòng)"""
        import time
        
        max_cycles = 2  # Số vòng xoay tối đa
        keys_per_cycle = len(self.api_keys)
        total_attempts = 0
        max_total_attempts = max_cycles * keys_per_cycle
        
        original_key_index = self.current_key_index  # Lưu vị trí ban đầu
        
        while total_attempts < max_total_attempts:
            try:
                prompt = f"""
Hãy dịch đoạn text sau sang tiếng Việt một cách tự nhiên và phù hợp với ngữ cảnh game:

Text: "{text}"

Yêu cầu:
- Dịch chính xác và tự nhiên cho game
- Giữ nguyên ý nghĩa gốc
- Sử dụng thuật ngữ game phù hợp
- KHÔNG ĐƯỢC dịch nội dung bên trong dấu ngoặc vuông [...] - giữ nguyên hoàn toàn
- Giữ nguyên các ký hiệu đặc biệt như [CGUIDE_INVALID], [C], [撤去/てっきょ] nếu có
- Chỉ trả về bản dịch, không giải thích
- Nếu text chứa ký tự Nhật Bản, hãy dịch phần có thể dịch được
- Ví dụ: "Hello [WORLD]" -> "Xin chào [WORLD]" (không dịch WORLD)
"""
                
                response = self.model.generate_content(prompt)
                translation = response.text.strip()
                
                # Loại bỏ dấu ngoặc kép nếu có
                if translation.startswith('"') and translation.endswith('"'):
                    translation = translation[1:-1]
                
                return translation
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Kiểm tra nếu là lỗi rate limit (429)
                if "429" in error_str or "quota" in error_str or "rate limit" in error_str or "resource_exhausted" in error_str:
                    total_attempts += 1
                    cycle_num = (total_attempts - 1) // keys_per_cycle + 1
                    
                    print(f"⚠️  Rate limit với key #{self.current_key_index + 1}. Chuyển ngay lập tức... (Vòng {cycle_num}, Lần {total_attempts}/{max_total_attempts})")
                    
                    # Chuyển sang key tiếp theo ngay lập tức
                    if not self.switch_to_next_key():
                        # Đã hết keys, quay về key đầu tiên để bắt đầu vòng mới
                        self.reset_to_first_key()
                        print(f"🔄 Bắt đầu vòng {cycle_num + 1}, quay về key #1")
                    
                    # Đợi 1 giây trước khi thử key mới
                    time.sleep(1)
                    continue
                else:
                    # Lỗi khác, không retry
                    print(f"❌ Lỗi khi dịch '{text}': {e}")
                    return text
        
        # Nếu đã thử hết tất cả keys trong tất cả vòng
        print(f"❌ Đã thử {max_cycles} vòng với tất cả {len(self.api_keys)} API keys. Bỏ qua từ: '{text}'")
        return text  # Trả về text gốc nếu không thể dịch
    
    def translate_text(self, text: str) -> tuple[str, str]:
        """
        Dịch một đoạn text
        
        Returns:
            tuple: (translated_text, source) - source có thể là 'dictionary', 'cache', 'gemini', 'skipped'
        """
        if not text or not text.strip():
            return text, 'skipped'
        
        text = text.strip()
        
        # 1. Kiểm tra từ điển trước
        dict_translation = self.get_translation_from_dictionary(text)
        if dict_translation:
            return dict_translation, 'dictionary'
        
        # 2. Kiểm tra cache
        cached_translation = self.get_translation_from_cache(text)
        if cached_translation:
            return cached_translation, 'cache'
        
        # 3. Dịch bằng Gemini
        translation = self.translate_with_gemini(text)
        
        # Lưu vào cache ngay lập tức
        self.cache[text] = translation
        self.save_cache()  # Lưu cache ngay sau khi dịch từng từ
        
        return translation, 'gemini'
    
    def translate_json_file(self, input_file: str, output_file: str = None):
        """Dịch một file JSON từ extract folder"""
        if not os.path.exists(input_file):
            print(f"❌ Không tìm thấy file: {input_file}")
            return
        
        if not output_file:
            output_file = input_file.replace('.json', '_vietnamese.json')
        
        print(f"\n📁 Đang dịch file: {input_file}")
        print(f"📄 File đầu ra: {output_file}")
        
        # Đọc file JSON
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ Lỗi khi đọc file {input_file}: {e}")
            return
        
        # Dịch từng entry trong text_entries
        text_entries = data.get('text_entries', [])
        total_entries = len(text_entries)
        
        if total_entries == 0:
            print("⚠️  Không có text entries để dịch")
            return
        
        print(f"📊 Tổng số entries: {total_entries}")
        print(f"📚 Từ điển có: {len(self.dictionary)} từ")
        print(f"💾 Cache có: {len(self.cache)} từ")
        print("\n🚀 Bắt đầu dịch...\n")
        
        start_time = time.time()
        
        for i, entry in enumerate(text_entries, 1):
            # Lấy text từ translated_text thay vì original_text
            current_text = entry.get('translated_text', '')
            original_text = entry.get('original_text', '')
            
            # Bỏ qua nếu không có text
            if not current_text or not current_text.strip():
                self.stats['skipped'] += 1
                continue
            
            # Dịch text hiện tại sang tiếng Việt
            translated_text, source = self.translate_text(current_text)
            entry['translated_text'] = translated_text
            
            # Cập nhật thống kê
            self.stats['total'] += 1
            if source == 'dictionary':
                self.stats['dictionary'] += 1
                icon = "📚"
            elif source == 'cache':
                self.stats['cached'] += 1
                icon = "💾"
            elif source == 'gemini':
                self.stats['translated'] += 1
                icon = "🤖"
            else:
                self.stats['skipped'] += 1
                icon = "⏭️"
            
            # Hiển thị tiến trình
            progress = (i / total_entries) * 100
            display_text = current_text[:50] + ('...' if len(current_text) > 50 else '')
            print(f"{icon} [{i:3d}/{total_entries}] ({progress:5.1f}%) {source:10s} | {display_text}")
            
            # Delay để tránh rate limit
            if source == 'gemini':
                time.sleep(0.5)  # 0.5 giây delay cho mỗi request
        
        # Lưu file đã dịch
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ Đã lưu file dịch: {output_file}")
        except Exception as e:
            print(f"❌ Lỗi khi lưu file: {e}")
            return
        
        # Lưu cache
        self.save_cache()
        
        # Hiển thị thống kê
        elapsed_time = time.time() - start_time
        self.print_statistics(elapsed_time)
    
    def batch_translate_folder(self, folder_path: str = "extract"):
        """Dịch tất cả file JSON trong folder extract"""
        if not os.path.exists(folder_path):
            print(f"❌ Không tìm thấy folder: {folder_path}")
            return
        
        # Tìm tất cả file JSON trong folder extract
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        
        if not json_files:
            print(f"❌ Không tìm thấy file JSON nào trong folder: {folder_path}")
            return
        
        print(f"🎯 Tìm thấy {len(json_files)} file JSON để dịch:")
        for file in json_files:
            print(f"  - {file}")
        
        # Tạo folder output
        output_folder = "translated"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            print(f"📁 Đã tạo folder: {output_folder}")
        
        # Reset thống kê cho batch
        self.stats = {
            'total': 0,
            'translated': 0,
            'cached': 0,
            'dictionary': 0,
            'skipped': 0
        }
        
        # Dịch từng file
        for json_file in json_files:
            input_path = os.path.join(folder_path, json_file)
            output_path = os.path.join(output_folder, json_file.replace('.json', '_vietnamese.json'))
            
            self.translate_json_file(input_path, output_path)
            print("\n" + "="*80 + "\n")
        
        # Hiển thị thống kê tổng
        print("\n🎉 HOÀN THÀNH DỊCH BATCH!")
        print(f"📁 Đã xử lý {len(json_files)} file")
        self.print_statistics(0)  # Không tính thời gian cho batch
    
    def print_statistics(self, elapsed_time: float):
        """In thống kê"""
        print("\n" + "="*60)
        print("📊 THỐNG KÊ DỊCH THUẬT")
        print("="*60)
        print(f"⏱️  Thời gian: {elapsed_time:.1f} giây")
        print(f"📝 Tổng số text: {self.stats['total']}")
        print(f"🤖 Dịch bằng Gemini: {self.stats['translated']}")
        print(f"💾 Lấy từ cache: {self.stats['cached']}")
        print(f"📚 Lấy từ từ điển: {self.stats['dictionary']}")
        print(f"⏭️  Bỏ qua: {self.stats['skipped']}")
        
        if self.stats['translated'] > 0:
            avg_time = elapsed_time / self.stats['translated']
            print(f"⚡ Trung bình: {avg_time:.1f}s/text")
        
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Auto Translator using Google Gemini API')
    parser.add_argument('action', choices=['translate', 'batch'], 
                       help='Hành động: translate (dịch 1 file) hoặc batch (dịch tất cả)')
    parser.add_argument('input_file', nargs='?', help='File JSON cần dịch (cho action translate)')
    parser.add_argument('-o', '--output', help='File đầu ra')
    parser.add_argument('--api-key', help='Google Gemini API key')
    
    args = parser.parse_args()
    
    try:
        translator = AutoTranslator(api_key=args.api_key)
        
        if args.action == 'translate':
            if not args.input_file:
                print("❌ Cần chỉ định file đầu vào cho action 'translate'")
                return
            
            translator.translate_json_file(args.input_file, args.output)
            
        elif args.action == 'batch':
            translator.batch_translate_folder()
            
    except ValueError as e:
        print(f"❌ {e}")
        print("\n💡 Hướng dẫn cài đặt API key:")
        print("   export GEMINI_API_KEY='your-api-key-here'")
        print("   hoặc dùng --api-key your-api-key-here")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()