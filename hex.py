import struct

def extract_file_size(path, offset=12):
    with open(path, 'rb') as f:
        f.seek(offset)
        data = f.read(4)
        return struct.unpack('<I', data)[0]

def write_file_size(path, new_file_size, offset=12):
    with open(path, 'r+b') as f:
        f.seek(offset)
        f.write(struct.pack('<I', new_file_size))

if __name__ == "__main__":
    file_path = './original/GDSMenuText.uasset'
    size = extract_file_size(file_path)
    print(f"File size at offset 12: {size}")
    # Để ghi giá trị mới, truyền đúng new_file_size:
    new_file_size = 1129485  # Thay bằng giá trị thực tế
    write_file_size(file_path, new_file_size)
    # Nếu cần thử offset khác:
    # size2 = extract_file_size(file_path, offset=16)
    # print(f"File size at offset 16: {size2}")
with open('./original/GDSMenuText.uasset', 'r+b') as f:
    f.seek(12)  # hoặc thử seek(16)
    f.write(struct.pack('<I', new_file_size))