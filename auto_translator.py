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
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️ OpenAI library không có. Cài đặt: pip install openai")

class AutoTranslator:
    def __init__(self, api_key: str = None, ai_engine: str = "gemini"):
        """
        Khởi tạo Auto Translator
        
        Args:
            api_key: API key cho AI engine được chọn
            ai_engine: Loại AI engine ("gemini" hoặc "chatgpt")
        """
        self.ai_engine = ai_engine.lower()
        
        if self.ai_engine not in ["gemini", "chatgpt"]:
            raise ValueError("ai_engine phải là 'gemini' hoặc 'chatgpt'")
        
        if self.ai_engine == "chatgpt" and not OPENAI_AVAILABLE:
            raise ValueError("OpenAI library chưa được cài đặt. Chạy: pip install openai")
        # Load danh sách API keys
        self.api_keys = self.load_api_keys()
        self.current_key_index = 0
        
        # Nếu có api_key truyền vào, ưu tiên sử dụng
        if api_key:
            self.api_keys.insert(0, api_key)
        
        if not self.api_keys:
            env_var = "OPENAI_API_KEY" if self.ai_engine == "chatgpt" else "GEMINI_API_KEY"
            raise ValueError(f"Cần có API key. Thêm vào file listkey.txt hoặc đặt biến môi trường {env_var}")
        
        # Cấu hình AI model với key đầu tiên
        self.setup_ai_model()
        
        # Cache và từ điển
        self.cache_file = "translation_cache.json"
        self.dictionary_file = "tudien.json"
        self.cache = self.load_cache()
        self.dictionary = self.load_dictionary()
        
        # Khởi tạo bảo vệ command tags
        self.initialize_command_tag_protection()
        
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
        env_var = "OPENAI_API_KEY" if self.ai_engine == "chatgpt" else "GEMINI_API_KEY"
        env_key = os.getenv(env_var)
        if env_key and env_key not in keys:
            keys.append(env_key)
            
        return keys
    
    def setup_ai_model(self):
        """Cấu hình AI model với API key hiện tại"""
        current_key = self.api_keys[self.current_key_index]
        
        if self.ai_engine == "gemini":
            genai.configure(api_key=current_key)
            self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
            print(f"🤖 Gemini - Sử dụng API key #{self.current_key_index + 1}/{len(self.api_keys)}")
        elif self.ai_engine == "chatgpt":
            # Không cần set openai.api_key global, sẽ dùng client pattern
            self.model_name = "gpt-3.5-turbo"
            print(f"🤖 ChatGPT - Sử dụng API key #{self.current_key_index + 1}/{len(self.api_keys)}")
    
    def setup_gemini_model(self):
        """Backward compatibility - redirect to setup_ai_model"""
        self.setup_ai_model()
    
    def switch_to_next_key(self) -> bool:
        """Chuyển sang API key tiếp theo. Trả về True nếu còn key khả dụng, False nếu đã hết danh sách"""
        self.current_key_index += 1
        if self.current_key_index < len(self.api_keys):
            self.setup_ai_model()
            return True
        return False
    
    def reset_to_first_key(self):
        """Reset về key đầu tiên để bắt đầu vòng mới"""
        self.current_key_index = 0
        self.setup_ai_model()
    
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
    
    def save_dictionary(self):
        """Lưu từ điển ra file tudien.json"""
        try:
            with open(self.dictionary_file, 'w', encoding='utf-8') as f:
                json.dump(self.dictionary, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  Lỗi khi lưu từ điển: {e}")
    
    def add_command_tags_to_dictionary(self):
        """Thêm các command tags vào từ điển để đảm bảo chúng không bị dịch"""
        import re
        
        # Danh sách các command tags phổ biến
        common_cmd_tags = [
            "<CMD_MENU_ENTER>", "<CMD_MENU_BACK>", "<CMD_MENU_EXIT>",
            "<CMD_MENU_SELECT>", "<CMD_MENU_CANCEL>", "<CMD_MENU_CONFIRM>",
            "<CMD_ATTACK>", "<CMD_DEFEND>", "<CMD_MOVE>", "<CMD_JUMP>",
            "<CMD_INTERACT>", "<CMD_USE>", "<CMD_INVENTORY>", "<CMD_MAP>",
            "<CMD_PAUSE>", "<CMD_SAVE>", "<CMD_LOAD>", "<CMD_SETTINGS>"
        ]
        
        # Tìm thêm command tags từ cache hiện tại
        cmd_pattern = r'<CMD_[^>]+>'
        found_tags = set()
        
        for text in self.cache.keys():
            tags = re.findall(cmd_pattern, text)
            found_tags.update(tags)
        
        # Kết hợp tất cả command tags
        all_cmd_tags = set(common_cmd_tags) | found_tags
        
        # Thêm vào từ điển (giữ nguyên)
        added_count = 0
        for tag in all_cmd_tags:
            tag_lower = tag.lower()
            if tag_lower not in self.dictionary:
                self.dictionary[tag_lower] = tag  # Giữ nguyên
                added_count += 1
        
        if added_count > 0:
            self.save_dictionary()
            print(f"📝 Đã thêm {added_count} command tags vào từ điển")
        
        return added_count
    
    def initialize_command_tag_protection(self):
        """Khởi tạo bảo vệ command tags: thêm vào từ điển và làm sạch cache"""
        print("🛡️ Khởi tạo bảo vệ command tags...")
        
        # Thêm command tags vào từ điển
        self.add_command_tags_to_dictionary()
        
        # Làm sạch cache
        self.clean_command_tags_from_cache()
        
        print("✅ Hoàn thành khởi tạo bảo vệ command tags")
    
    def get_translation_from_dictionary(self, text: str) -> Optional[str]:
        """Kiểm tra xem text có trong từ điển không"""
        text_lower = text.lower().strip()
        return self.dictionary.get(text_lower)
    
    def get_translation_from_cache(self, text: str) -> Optional[str]:
        """Lấy bản dịch từ cache"""
        return self.cache.get(text)
    
    def clean_command_tags_from_cache(self):
        """Làm sạch cache, loại bỏ các command tags đã bị dịch sai"""
        import re
        
        cmd_pattern = r'<CMD_[^>]+>'
        cleaned_count = 0
        
        # Tạo danh sách các key cần xóa
        keys_to_remove = []
        
        for original_text, translated_text in self.cache.items():
            # Kiểm tra nếu text gốc chứa command tags
            original_cmds = re.findall(cmd_pattern, original_text)
            
            if original_cmds:
                # Kiểm tra nếu bản dịch không chứa command tags (đã bị dịch sai)
                translated_cmds = re.findall(cmd_pattern, translated_text)
                
                if len(original_cmds) != len(translated_cmds) or set(original_cmds) != set(translated_cmds):
                    keys_to_remove.append(original_text)
                    cleaned_count += 1
                    print(f"🧹 Xóa cache sai: '{original_text}' -> '{translated_text}'")
        
        # Xóa các entries sai
        for key in keys_to_remove:
            del self.cache[key]
        
        if cleaned_count > 0:
            self.save_cache()
            print(f"✅ Đã làm sạch {cleaned_count} entries trong cache")
        else:
            print("✅ Cache đã sạch, không có command tags bị dịch sai")
        
        return cleaned_count
    

    def validate_command_tags(self, original: str, translated: str) -> str:
        """Kiểm tra và khôi phục command tags nếu bị dịch nhầm"""
        import re
        
        # Tìm tất cả command tags trong text gốc
        cmd_pattern = r'<CMD_[^>]+>'
        original_cmds = re.findall(cmd_pattern, original)
        
        # Nếu có command tags trong text gốc
        if original_cmds:
            for cmd in original_cmds:
                if cmd not in translated:
                    print(f"⚠️  Phát hiện command tag bị mất hoặc dịch: {cmd}")
                    # Tìm và thay thế các phiên bản đã dịch
                    # Ví dụ: nếu <CMD_MENU_ENTER> bị dịch thành "Vào menu"
                    # thì ta cần khôi phục lại
                    if "menu" in translated.lower() and "CMD_MENU" in cmd:
                        # Thay thế các từ có thể là bản dịch của command
                        translated = re.sub(r'[Vv]ào menu|[Ee]nter menu|[Mm]enu enter', cmd, translated)
                    elif "back" in translated.lower() and "CMD_MENU_BACK" in cmd:
                        translated = re.sub(r'[Tt]rở lại|[Bb]ack|[Qq]uay lại', cmd, translated)
                    elif "jump" in translated.lower() and "CMD_JUMP" in cmd:
                        translated = re.sub(r'[Nn]hảy|[Jj]ump', cmd, translated)
                    else:
                        # Nếu không tìm thấy, thêm command tag vào cuối
                        translated = f"{translated} {cmd}"
        
        return translated

    def translate_with_gemini(self, text: str) -> str:
        """Dịch text bằng Google Gemini với bối cảnh game và multiple API keys (xoay vòng)"""
        import time
        
        max_cycles = 1000005  # Số vòng xoay tối đa
        keys_per_cycle = len(self.api_keys)
        total_attempts = 0
        max_total_attempts = max_cycles * keys_per_cycle
        
        original_key_index = self.current_key_index  # Lưu vị trí ban đầu
        
        while total_attempts < max_total_attempts:
            try:
                prompt = f"""
Hãy dịch đoạn text sau sang tiếng Việt một cách tự nhiên và phù hợp với ngữ cảnh game:

Text: "{text}"

Yêu cầu QUAN TRỌNG:
- Dịch chính xác và tự nhiên cho game
- Giữ nguyên ý nghĩa gốc
- Sử dụng thuật ngữ game phù hợp
- **TUYỆT ĐỐI KHÔNG ĐƯỢC dịch bất kỳ nội dung nào bên trong:**
  * Dấu ngoặc vuông [...] - giữ nguyên hoàn toàn
  * Dấu ngoặc nhọn <...> - giữ nguyên hoàn toàn
  * Các command tags như <CMD_MENU_ENTER>, <CMD_MENU_BACK>, <CMD_JUMP>, <CMD_BTL_ATTACK>, v.v.
- Giữ nguyên hoàn toàn các ký hiệu đặc biệt và command tags
- Chỉ trả về bản dịch, không giải thích
- Nếu text chứa ký tự Nhật Bản, hãy dịch phần có thể dịch được

Ví dụ CHÍNH XÁC:
- "Press <CMD_MENU_ENTER> to continue" -> "Nhấn <CMD_MENU_ENTER> để tiếp tục"
- "<CMD_MENU_BACK>" -> "<CMD_MENU_BACK>" (KHÔNG dịch thành "Trở lại")
- "[CGUIDE_INVALID]<CMD_MENU_BACK>[C]" -> "[CGUIDE_INVALID]<CMD_MENU_BACK>[C]"
- "Hello [WORLD]" -> "Xin chào [WORLD]"
- "Jump with <CMD_JUMP>" -> "Nhảy bằng <CMD_JUMP>"

LƯU Ý: Nếu text chỉ chứa command tag (như "<CMD_MENU_ENTER>"), hãy trả về CHÍNH XÁC như vậy, KHÔNG dịch.
"""
                
                response = self.model.generate_content(prompt)
                translation = response.text.strip()
                
                # Loại bỏ dấu ngoặc kép nếu có
                if translation.startswith('"') and translation.endswith('"'):
                    translation = translation[1:-1]
                
                # Kiểm tra cuối cùng: nếu translation vẫn chứa text gốc, loại bỏ nó
                if text in translation and translation != text:
                    # Nếu translation chứa text gốc, tìm và loại bỏ
                    if translation.startswith(text):
                        remaining = translation[len(text):].strip()
                        if remaining.startswith('" -> "') or remaining.startswith(' -> '):
                            translation = remaining.split('"')[-1] if '"' in remaining else remaining.split(' -> ')[-1]
                            translation = translation.strip().strip('"')
                
                # Validate và khôi phục command tags nếu cần
                translation = self.validate_command_tags(text, translation)
                
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
    
    def translate_with_chatgpt(self, text: str) -> str:
        """Dịch text bằng ChatGPT GPT-3.5-turbo với multiple API keys (xoay vòng)"""
        import time
        
        max_cycles = 5  # Số vòng xoay tối đa
        keys_per_cycle = len(self.api_keys)
        total_attempts = 0
        max_total_attempts = max_cycles * keys_per_cycle
        
        original_key_index = self.current_key_index  # Lưu vị trí ban đầu
        
        while total_attempts < max_total_attempts:
            try:
                prompt = f"""Dịch text sau sang tiếng Việt cho game. CHỈ trả về bản dịch, KHÔNG bao gồm text gốc hay ký hiệu "->".

Text cần dịch: "{text}"

Quy tắc:
- Dịch tự nhiên cho game
- Giữ nguyên [...] và <...>
- Giữ nguyên command tags như <CMD_MENU_ENTER>
- CHỈ trả về bản dịch tiếng Việt
- KHÔNG viết dạng "text gốc -> bản dịch"
- KHÔNG giải thích

Ví dụ đúng:
Input: "Press <CMD_MENU_ENTER> to continue"
Output: "Nhấn <CMD_MENU_ENTER> để tiếp tục"

Input: "<CMD_MENU_BACK>"
Output: "<CMD_MENU_BACK>"

Input: "Hello [WORLD]"
Output: "Xin chào [WORLD]"

Bản dịch:"""
                
                # Sử dụng OpenAI API v1.0+
                client = openai.OpenAI(api_key=self.api_keys[self.current_key_index])
                
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "Bạn là một chuyên gia dịch thuật game, chuyên dịch từ tiếng Anh sang tiếng Việt."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                translation = response.choices[0].message.content.strip()
                
                # Loại bỏ dấu ngoặc kép nếu có
                if translation.startswith('"') and translation.endswith('"'):
                    translation = translation[1:-1]
                
                # Xử lý nếu ChatGPT trả về format "text gốc -> bản dịch"
                if ' -> ' in translation:
                    # Lấy phần sau dấu ->
                    translation = translation.split(' -> ')[-1].strip()
                    # Loại bỏ dấu ngoặc kép nếu có
                    if translation.startswith('"') and translation.endswith('"'):
                        translation = translation[1:-1]
                elif '" -> "' in translation:
                    # Xử lý format "text" -> "dịch"
                    parts = translation.split('" -> "')
                    if len(parts) >= 2:
                        translation = parts[-1].rstrip('"')
                elif translation.startswith(f'"{text}"'):
                    # Xử lý nếu bắt đầu bằng text gốc trong ngoặc kép
                    translation = translation[len(f'"{text}"'):].strip()
                    if translation.startswith(' -> '):
                        translation = translation[4:].strip()
                    if translation.startswith('"') and translation.endswith('"'):
                        translation = translation[1:-1]
                
                # Validate và khôi phục command tags nếu cần
                translation = self.validate_command_tags(text, translation)
                
                return translation
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Kiểm tra nếu là lỗi rate limit
                if "rate limit" in error_str or "quota" in error_str or "429" in error_str or "too many requests" in error_str:
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
        
        # 3. Dịch bằng AI engine được chọn
        if self.ai_engine == "gemini":
            translation = self.translate_with_gemini(text)
        elif self.ai_engine == "chatgpt":
            translation = self.translate_with_chatgpt(text)
        else:
            translation = text  # Fallback
        
        # Lưu vào cache ngay lập tức
        self.cache[text] = translation
        self.save_cache()  # Lưu cache ngay sau khi dịch từng từ
        
        return translation, self.ai_engine
    
    def translate_json_file(self, input_file: str, output_file: str = None):
        """Dịch một file JSON từ extract folder"""
        if not os.path.exists(input_file):
            print(f"❌ Không tìm thấy file: {input_file}")
            return
        
        if not output_file:
            output_file = input_file.replace('.json', '.json')
        
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
            if source in ['gemini', 'chatgpt']:
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
            output_path = os.path.join(output_folder, json_file.replace('.json', '.json'))
            
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
        print(f"🤖 Dịch bằng {self.ai_engine.upper()}: {self.stats['translated']}")
        print(f"💾 Lấy từ cache: {self.stats['cached']}")
        print(f"📚 Lấy từ từ điển: {self.stats['dictionary']}")
        print(f"⏭️  Bỏ qua: {self.stats['skipped']}")
        
        if self.stats['translated'] > 0:
            avg_time = elapsed_time / self.stats['translated']
            print(f"⚡ Trung bình: {avg_time:.1f}s/text")
        
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Auto Translator using Google Gemini API or ChatGPT API')
    parser.add_argument('action', choices=['translate', 'batch'], 
                       help='Hành động: translate (dịch 1 file) hoặc batch (dịch tất cả)')
    parser.add_argument('input_file', nargs='?', help='File JSON cần dịch (cho action translate)')
    parser.add_argument('-o', '--output', help='File đầu ra')
    parser.add_argument('--api-key', help='API key cho AI engine được chọn')
    parser.add_argument('--ai-engine', choices=['gemini', 'chatgpt'], default='gemini',
                       help='AI engine để dịch: gemini (mặc định) hoặc chatgpt')
    
    args = parser.parse_args()
    
    try:
        translator = AutoTranslator(api_key=args.api_key, ai_engine=args.ai_engine)
        
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
        print("   Cho Gemini: export GEMINI_API_KEY='your-gemini-key-here'")
        print("   Cho ChatGPT: export OPENAI_API_KEY='your-openai-key-here'")
        print("   hoặc dùng --api-key your-api-key-here --ai-engine [gemini|chatgpt]")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()