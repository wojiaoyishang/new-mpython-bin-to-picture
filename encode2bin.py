import os
from PIL import Image, ImageDraw, ImageFont

def process_image(img):
    img_gray = img.convert("L")
    threshold = 127
    img_binary = img_gray.point(lambda x: 0 if x < threshold else 1)
    
    return img_binary.size[0], list(img_binary.getdata())
    
def encode_image_data(image_data):
    encoded_data = bytearray()
    count = 0
    now_c = 0
    if image_data[0] == 1:
        encoded_data.append(0x00)
    for b in image_data:
        if b == now_c:
            count += 1
        else:
            encoded_data.append(count)
            count = 1
            now_c = 1 - now_c
        if count >= 0xFE:
            encoded_data.append(count)
            encoded_data.append(0x00)
            count = 1
    
    encoded_data.append(count)
    return encoded_data

def write_to_bin(target_image_name, img_width, img_encode_data, img_bin_path, only_add=False):
    """
    向bin文件中写入或更新指定文件名的数据
    :param target_image_name: 写入bin文件的文件名
    :param img_width: 图片宽度
    :param img_encode_data: 图片的编码数据，也就是bin文件中的data
    :param img_bin_path: bin文件路径
    :param only_add: 如果为True为只追加模式，不检测是否已有相同文件名
    """

    # 如果文件不存在或者只是添加模式，直接在尾部添加数据
    if only_add or not os.path.isfile(img_bin_path):
        with open(img_bin_path, "ab") as f:  # 以二进制追加模式打开文件
            f.write(b'\xff' + target_image_name.encode('utf-8'))  # 写入文件名
            f.write(b'\xff' + str(img_width).encode('utf-8'))  # 写入图片宽度
            f.write(b'\xff' + img_encode_data)  # 写入图片数据
    else:
        # 否则，需要更新数据
        with open(img_bin_path, "rb+") as f:
            # 先读取所有的数据
            data = f.read()

            # 将数据分割成文件名、宽度和数据
            files_data = data.split(b'\xff')[1:]  # 去掉最前面的空字符

            # 将数据组织成元组（文件名，宽度，数据）
            files_data = [(files_data[i].decode('utf-8'), files_data[i+1].decode('utf-8'), files_data[i+2]) for i in range(0, len(files_data), 3)]

            # 查找是否有相同的文件名
            for i, (filename, width, img_data) in enumerate(files_data):
                if filename == target_image_name:
                    del files_data[i]  # 删除旧的数据
                    break
            
            # 在尾部添加新的数据
            files_data.append((target_image_name, str(img_width), img_encode_data))

            # 清空文件
            f.seek(0)
            f.truncate()

            # 重新写入所有的数据
            for filename, width, img_data in files_data:
                f.write(b'\xff' + filename.encode('utf-8'))  # 写入文件名
                f.write(b'\xff' + width.encode('utf-8'))  # 写入图片宽度
                f.write(b'\xff' + img_data)  # 写入图片数据

def font_to_bin(font_path, font_size, img_bin_path, chs=""):
    # 加载字体文件
    font = ImageFont.truetype(font_path, font_size)

    unicode_range = list(range(0x20, 0x7F))  # ASCII符号，数字和字母

    for s in chs:
        unicode_range.append(ord(s))

    # 对每一个unicode字符进行处理
    for unicode_char in unicode_range:
        # 获取字符的宽度
        char_width, char_height = font.getsize(chr(unicode_char))

        # 创建一个新的图片，宽度等于字符的宽度
        img = Image.new('RGB', (char_width, char_height), color=(255, 255, 255))
        d = ImageDraw.Draw(img)

        # 在图片上绘制字符
        d.text((0,0), chr(unicode_char), fill=(0, 0, 0), font=font)

        # 使用process_image和encode_image_data处理图片
        img_width, img_data = process_image(img)
        img_encode_data = encode_image_data(img_data)

        # 使用write_to_bin将数据写入bin文件
        write_to_bin(chr(unicode_char), img_width, img_encode_data, img_bin_path, only_add=True)
