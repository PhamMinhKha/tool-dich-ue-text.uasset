#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Auto Translator
Hướng dẫn sử dụng chương trình dịch tự động
"""

import os
import json

def create_sample_dictionary():
    """Tạo file từ điển mẫu"""
    sample_dict = {
        "exit": "Thoát",
        "craft": "Chế tạo",
        "mode": "Chế độ",
        "build": "Xây dựng",
        "chest": "Rương",
        "options": "Tùy chọn",
        "network": "Mạng",
        "error": "Lỗi",
        "connection": "Kết nối",
        "player": "Người chơi",
        "name": "Tên",
        "enter": "Nhập",
        "comment": "Bình luận",
        "gift": "Quà tặng",
        "code": "Mã",
        "find": "Tìm",
        "place": "Nơi",
        "here": "Đây",
        "contains": "Chứa",
        "prohibited": "Cấm",
        "words": "Từ"
    }
    
    with open('tudien.json', 'w', encoding='utf-8') as f:
        json.dump(sample_dict, f, ensure_ascii=False, indent=4)
    
    print("✅ Đã tạo file tudien.json với các từ mẫu")

def show_usage_examples():
    """Hiển thị các ví dụ sử dụng"""
    print("\n" + "="*60)
    print("🚀 HƯỚNG DẪN SỬ DỤNG AUTO TRANSLATOR")
    print("="*60)
    
    print("\n📋 CÁC BƯỚC THỰC HIỆN:")
    print("\n1️⃣  Cài đặt thư viện:")
    print("   pip3 install -r requirements.txt")
    
    print("\n2️⃣  Lấy API Key từ Google AI Studio:")
    print("   - Truy cập: https://makersuite.google.com/app/apikey")
    print("   - Tạo API key mới")
    print("   - Copy API key")
    
    print("\n3️⃣  Cài đặt API Key:")
    print("   export GEMINI_API_KEY='your-api-key-here'")
    
    print("\n4️⃣  Trích xuất text từ game:")
    print("   python3 uasset_text_extractor.py batch-extract")
    
    print("\n5️⃣  Dịch tự động:")
    print("   # Dịch tất cả file")
    print("   python3 auto_translator.py batch")
    print("   ")
    print("   # Hoặc dịch từng file")
    print("   python3 auto_translator.py translate extract/GDSSystemText_texts.json")
    
    print("\n6️⃣  Tạo file game đã dịch:")
    print("   python3 uasset_text_extractor.py batch-import")
    
    print("\n📚 TỪ ĐIỂN (tudien.json):")
    print("   - Chứa các từ đã dịch sẵn")
    print("   - Ưu tiên cao nhất, không cần dịch lại")
    print("   - Format: {\"english_word\": \"từ_tiếng_việt\"}")
    
    print("\n💾 CACHE (translation_cache.json):")
    print("   - Tự động lưu các từ đã dịch")
    print("   - Tránh dịch lại, tiết kiệm API calls")
    print("   - Tự động tạo khi chạy lần đầu")
    
    print("\n📁 CẤU TRÚC THƯ MỤC SAU KHI DỊCH:")
    print("   DichGame/")
    print("   ├── extract/              # File JSON gốc")
    print("   ├── translated/           # File JSON đã dịch")
    print("   ├── import/               # File .uasset đã dịch")
    print("   ├── tudien.json           # Từ điển")
    print("   ├── translation_cache.json # Cache")
    print("   └── auto_translator.py    # Chương trình dịch")
    
    print("\n⚡ TIPS:")
    print("   - Thêm từ vào tudien.json để dịch nhanh hơn")
    print("   - Cache sẽ lưu lại, lần sau dịch nhanh hơn")
    print("   - Có thể dừng và tiếp tục dịch bất cứ lúc nào")
    print("   - Kiểm tra file translated/ trước khi import")
    
    print("\n" + "="*60)

def check_environment():
    """Kiểm tra môi trường"""
    print("\n🔍 KIỂM TRA MÔI TRƯỜNG:")
    
    # Kiểm tra Python
    import sys
    print(f"✅ Python: {sys.version.split()[0]}")
    
    # Kiểm tra thư viện
    try:
        import google.generativeai
        print("✅ google-generativeai: Đã cài đặt")
    except ImportError:
        print("❌ google-generativeai: Chưa cài đặt")
        print("   Chạy: pip3 install -r requirements.txt")
    
    # Kiểm tra API key
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"✅ GEMINI_API_KEY: Đã cài đặt ({api_key[:10]}...)")
    else:
        print("❌ GEMINI_API_KEY: Chưa cài đặt")
        print("   Chạy: export GEMINI_API_KEY='your-api-key'")
    
    # Kiểm tra file
    files_to_check = [
        ('uasset_text_extractor.py', 'Chương trình trích xuất'),
        ('auto_translator.py', 'Chương trình dịch tự động'),
        ('requirements.txt', 'Danh sách thư viện'),
        ('tudien.json', 'Từ điển')
    ]
    
    for filename, description in files_to_check:
        if os.path.exists(filename):
            print(f"✅ {filename}: {description}")
        else:
            print(f"❌ {filename}: Không tìm thấy")
    
    # Kiểm tra folder
    folders = ['extract', 'translated', 'import', 'original']
    for folder in folders:
        if os.path.exists(folder):
            file_count = len([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
            print(f"📁 {folder}/: {file_count} files")
        else:
            print(f"📁 {folder}/: Chưa tạo")

def main():
    print("🎮 DEMO AUTO TRANSLATOR - DỊCH GAME TỰ ĐỘNG")
    
    # Tạo từ điển mẫu nếu chưa có
    if not os.path.exists('tudien.json'):
        create_sample_dictionary()
    
    # Kiểm tra môi trường
    check_environment()
    
    # Hiển thị hướng dẫn
    show_usage_examples()
    
    print("\n🎯 SẴN SÀNG DỊCH GAME!")
    print("\n💡 Chạy lệnh sau để bắt đầu:")
    print("   python3 auto_translator.py batch")

if __name__ == "__main__":
    main()