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
            api_key: Google Gemini API key. Nếu không có, sẽ đọc từ biến môi trường GEMINI_API_KEY
        """
        self.api_key = api_key or os.getenv('AIzaSyDpEdBfTvHCc1d9XMnzsFq2nXpzTEj1DKU')
        if not self.api_key:
            raise ValueError("Cần có GEMINI_API_KEY. Đặt biến môi trường hoặc truyền vào constructor.")
        
        # Cấu hình Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-pro')
        
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
        """Dịch text bằng Google Gemini"""
        try:
            prompt = f"""
Hãy dịch đoạn text sau sang tiếng Việt một cách tự nhiên và phù hợp với ngữ cảnh game:

Text: "{text}"

Yêu cầu:
- Dịch chính xác và tự nhiên
- Giữ nguyên ý nghĩa gốc
- Phù hợp với thuật ngữ game
- Chỉ trả về bản dịch, không giải thích
"""
            
            response = self.model.generate_content(prompt)
            translation = response.text.strip()
            
            # Loại bỏ dấu ngoặc kép nếu có
            if translation.startswith('"') and translation.endswith('"'):
                translation = translation[1:-1]
            
            return translation
            
        except Exception as e:
            print(f"❌ Lỗi khi dịch '{text}': {e}")
            return text  # Trả về text gốc nếu lỗi
    
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
        
        # Lưu vào cache
        self.cache[text] = translation
        
        return translation, 'gemini'
    
    def translate_json_file(self, input_file: str, output_file: str = None):
        """Dịch một file JSON"""
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
        
        # Dịch từng entry
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
            original_text = entry.get('original_text', '')
            
            if not original_text or not original_text.strip():
                self.stats['skipped'] += 1
                continue
            
            # Dịch text
            translated_text, source = self.translate_text(original_text)
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
            print(f"{icon} [{i:3d}/{total_entries}] ({progress:5.1f}%) {source:10s} | {original_text[:50]}{'...' if len(original_text) > 50 else ''}")
            
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
        """Dịch tất cả file JSON trong folder"""
        if not os.path.exists(folder_path):
            print(f"❌ Không tìm thấy folder: {folder_path}")
            return
        
        # Tìm tất cả file JSON
        json_files = [f for f in os.listdir(folder_path) if f.endswith('_texts.json')]
        
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
        
        # Dịch từng file
        for json_file in json_files:
            input_path = os.path.join(folder_path, json_file)
            output_path = os.path.join(output_folder, json_file.replace('_texts.json', '_vietnamese.json'))
            
            self.translate_json_file(input_path, output_path)
            print("\n" + "="*80 + "\n")
    
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