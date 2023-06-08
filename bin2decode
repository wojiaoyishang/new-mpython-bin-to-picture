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