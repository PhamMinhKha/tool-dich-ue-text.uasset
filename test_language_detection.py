#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from uasset_text_extractor import UAssetTextExtractor

def test_language_detection():
    extractor = UAssetTextExtractor()
    
    test_cases = [
        ("What's that, buddy? You found an Eternian Flying Fish? You heard him, pal! Let's hit the water!", "english"),
        ("Es scheinen jedoch noch nicht alle bereit zu sein", "german"),
        ("Es scheinen jedoch noch nicht alle bereit zu sein.", "german"),
        ("Hello world", "english"),
        ("Bonjour le monde", "french"),
        ("Hola mundo", "spanish"),
        ("Ciao mondo", "italian"),
        ("Xin chào thế giới", "vietnamese")
    ]
    
    print("Testing language detection:")
    print("=" * 50)
    
    for text, expected in test_cases:
        detected = extractor._detect_language(text)
        status = "✅" if detected == expected else "❌"
        print(f"{status} Text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print(f"   Expected: {expected}, Detected: {detected}")
        print()

if __name__ == '__main__':
    test_language_detection()