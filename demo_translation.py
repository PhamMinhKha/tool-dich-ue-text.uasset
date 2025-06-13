#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo Translation Script
Script demo để test dịch thuật một vài text mẫu
"""

import json
import os
from uasset_text_extractor import UAssetTextExtractor

def create_demo_translation():
    """Tạo file demo với một vài text đã dịch sẵn"""
    
    # Đọc file JSON gốc
    json_file = "GDSSystemText_texts.json"
    if not os.path.exists(json_file):
        print(f"Không tìm thấy file {json_file}")
        print("Hãy chạy extract trước: python3 uasset_text_extractor.py extract GDSSystemText.uasset")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Dictionary dịch thuật mẫu
    translations = {
        "Exit Craft Mode?": "Thoát chế độ xây dựng?",
        "Exit Hagram Build?": "Thoát chế độ xây dựng Hagram?",
        "Build here?": "Xây dựng ở đây?",
        "That contains prohibited words.": "Có chứa từ bị cấm.",
        "That contains prohibited characters.": "Có chứa ký tự bị cấm.",
        "Names must contain letters.": "Tên phải chứa chữ cái.",
        "Kanji cannot be used.": "Không thể sử dụng Kanji.",
        "Numbers must be six or fewer digits.": "Số phải có 6 chữ số hoặc ít hơn.",
        "Please enter a name.": "Vui lòng nhập tên.",
        "Enter the player name you wish to search.": "Nhập tên người chơi bạn muốn tìm.",
        "Enter the island name you wish to search.": "Nhập tên đảo bạn muốn tìm.",
        "Enter a gift code.": "Nhập mã quà tặng.",
        "Enter a comment.": "Nhập bình luận.",
        "Your name will be shared with online players.": "Tên của bạn sẽ được chia sẻ với người chơi online.",
        "Communication failed.": "Kết nối thất bại.",
        "The adventure has come to an end.": "Cuộc phiêu lưu đã kết thúc.",
        "The connection has been interrupted.": "Kết nối đã bị gián đoạn.",
        "Ending connection.": "Đang kết thúc kết nối.",
        "Connecting...": "Đang kết nối...",
        "Player Data": "Dữ liệu người chơi",
        "System Data": "Dữ liệu hệ thống",
        "Hagram can't come back here.": "Hagram không thể quay lại đây.",
        "Find a bigger space.": "Tìm một không gian lớn hơn."
    }
    
    # Áp dụng dịch thuật
    translated_count = 0
    for entry in data['text_entries']:
        original = entry['original_text']
        if original in translations:
            entry['translated_text'] = translations[original]
            entry['language'] = 'vietnamese'  # Cập nhật ngôn ngữ
            translated_count += 1
            print(f"Dịch: '{original}' -> '{translations[original]}'")
    
    # Lưu file demo
    demo_file = "GDSSystemText_texts_demo_vietnamese.json"
    with open(demo_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\nĐã tạo file demo: {demo_file}")
    print(f"Đã dịch {translated_count} text entries")
    
    return demo_file

def create_translated_uasset(demo_file):
    """Tạo file .uasset với text đã dịch"""
    
    extractor = UAssetTextExtractor()
    
    # Đọc file JSON demo
    json_data = extractor.import_from_json(demo_file)
    if not json_data:
        print("Không thể đọc file JSON demo")
        return
    
    # Đọc lại file gốc
    original_uasset = json_data.get('file_info', {}).get('original_file')
    if not original_uasset or not os.path.exists(original_uasset):
        print("Không tìm thấy file .uasset gốc")
        return
    
    extractor.extract_texts(original_uasset)
    
    # Tạo file .uasset mới
    output_file = "GDSSystemText_vietnamese_demo.uasset"
    print(f"\nĐang tạo file .uasset tiếng Việt: {output_file}")
    extractor.rebuild_uasset(json_data, output_file)
    
    return output_file

def main():
    print("=== DEMO DỊCH THUẬT UASSET ===")
    print("Script này sẽ tạo một file demo với text tiếng Việt")
    print()
    
    # Bước 1: Tạo file JSON demo với text đã dịch
    print("Bước 1: Tạo file JSON demo với text tiếng Việt...")
    demo_file = create_demo_translation()
    
    if not demo_file:
        return
    
    # Bước 2: Tạo file .uasset mới
    print("\nBước 2: Tạo file .uasset mới với text tiếng Việt...")
    output_file = create_translated_uasset(demo_file)
    
    if output_file:
        print(f"\n✅ HOÀN THÀNH!")
        print(f"📁 File JSON demo: {demo_file}")
        print(f"🎮 File .uasset tiếng Việt: {output_file}")
        print()
        print("Bạn có thể:")
        print(f"1. Mở {demo_file} để xem/chỉnh sửa bản dịch")
        print(f"2. Sử dụng {output_file} thay thế file gốc trong game")
        print(f"3. Backup file gốc trước khi thay thế!")
    else:
        print("❌ Có lỗi xảy ra khi tạo file .uasset")

if __name__ == '__main__':
    main()