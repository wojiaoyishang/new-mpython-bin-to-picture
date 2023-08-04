import sys
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

def print_from_bin(bin_file_path, target_image_name):

    target_image_name = target_image_name.encode('utf-8')
    
    with open(bin_file_path, "rb") as f:
        b = f.read(1)  # 跳过一个字节，是开头的 0xff
        temp = bytearray()
        empty_times = 0  # 0x00 的出现次数，用于定位数据段
        found, image_width, image_height = False, 0, 0
        point_count = 0  # 一行已打印的个数
        c = 0  # 判断打印是 1 还是 0 
        
        while b:
            if b == b'\xff':
                if empty_times % 3 == 1 and temp == target_image_name:  # 图片名称
                    found = True
                    print("编码位置：", f.tell() - len(target_image_name) - 2)
                elif found and empty_times % 3 == 2: # 图片宽度
                    image_width = int(temp.decode('utf-8'))
                elif found and empty_times % 3 == 0: # 读完数据
                    break
                empty_times += 1
                temp.clear()
            else:
                if not found and empty_times % 3 == 1:  # 图片文件名读取
                    temp.extend(b)
                elif found and empty_times % 3 == 2:  # 图片宽度读取
                    temp.extend(b)
                elif found and empty_times % 3 == 0:
                    t = int.from_bytes(b, "big")
                    c = str(c)
                    
                    while t > 0:
                        if image_width - point_count <= t:
                            print(c * (image_width - point_count))
                            t -= image_width - point_count
                            point_count = 0
                            image_height += 1
                        else:
                            print(c * t, end="")
                            point_count += t
                            t -= t
                    
                    c = 1 - int(c)
            b = f.read(1)
            
        return image_width, image_height

if len(sys.argv) != 4:
    print("参数不正确！使用方法：python picture2binM.py 图片名 标识名 bin文件名")
    exit()
print("编码文件：", sys.argv[1])
print("编码标识：", sys.argv[2])
print("目标bin文件：", sys.argv[3])

with Image.open(sys.argv[1]) as I:
    width, data = process_image(I)
    data = encode_image_data(data)
    write_to_bin(sys.argv[2], width, data, sys.argv[3])

print_from_bin(sys.argv[3], sys.argv[2])
