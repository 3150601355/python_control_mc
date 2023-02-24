import os
import sys
import time
import math
from PIL import Image


from mcpi.minecraft import Minecraft
import mcpi.block as block

############################
# 以下变量和每次具体任务有关

SAMPLE_FOLDER = "SAMPLE_FOLDER"         # 用来采样颜色的图片
dictSampleColor = dict()                # (r,g,b) as key, int as value
dictColor256ToMaterail = dict()

# 读取全部图片,生成颜色查找表
def loadColorMap(folderPath):
    lstFileName = os.listdir(folderPath)

    for fileName in lstFileName:
        fullPath = os.path.join(folderPath, fileName)
        if os.path.isfile(fullPath):
            _loadFile(fullPath)

    # 对256色中的每一种，指定一个材质
    #   256色模式： 共8 bits (R: 3 bits; G: 3 bits; B: 2 bits)。
    for r in range(8):
        for g in range(8):
            for b in range(4):
                value = _findNearestByRgb(r, g, b)
                key = (r, g, b)
                dictColor256ToMaterail.update({key : value})


def _loadFile(fullPath):
    im = Image.open(fullPath)
    
    # 计算key值(r,g,b)
    r, g, b = _calAverageRgb(im)
    r >>= 5; g >>= 5; b >>=6

    # 文件名中包含id和序号，如 35-2
    fileName = fullPath.split(os.sep)[-1][:-4]  

    # 改为turtle (35,2)的形式
    arr = fileName.split('-')
    tt = ( int(arr[0]), int(arr[1]) )

    #放入词典，样式：{(r, g, b), (材质ID, 子材质序号)}
    dictSampleColor.update({(r, g, b): tt})


# (LAB颜色空间)
def _colorDistance(rgb1, rgb2):
    R_1,G_1,B_1 = rgb1
    R_2,G_2,B_2 = rgb2
    rmean = (R_1+R_2)/2
    R = R_1-R_2
    G = G_1-G_2
    B = B_1-B_2

    return math.sqrt((2+rmean/256)*(R**2)+4*(G**2)+(2+(255-rmean)/256)*(B**2))
    

# 计算平均rgb值
def _calAverageRgb(im):
    if im.mode != "RGB":
        im = im.convert("RGB")

    pix = im.load()
    avgR, avgG, avgB = 0, 0, 0
    n = 1
    for i in range(im.size[0]):
        for j in range(im.size[1]):
            r, g, b = pix[i, j]
            avgR += r
            avgG += g
            avgB += b
            n += 1

    return (avgR//n, avgG//n, avgB//n)
   
   
# 获取颜色最接近的方块
def _findNearestByRgb(r, g, b):
    minError = 3*255*255 # 初值为最大误差
    k = ""
    for key in dictSampleColor.keys():
        R, G, B = key
        # 计算颜色误差，用平方差的和来表示。其实用HSV色系更好，但是考虑到MC只有16色，还要啥自行车啊
        cur_dif =   _colorDistance( (r,g,b), (R,G,B) )
        if cur_dif < minError:
            minError = cur_dif
            k = key

    return dictSampleColor[k]  


def init():
    global mc, x, y, z

    print('加载颜色样图...')
    loadColorMap(SAMPLE_FOLDER)

    print('连接MC...')
    mc = Minecraft.create()
    x, y, z = mc.player.getTilePos()


def drawFrame(img):
    imgW, imgH = img.size
    mode = img.mode

    zDistance = (imgW * 100) // 256

    for row in range(imgH):
        for col in range(imgW):
            # img中每个点的颜色分量
            r, g, b, alpha = img.getpixel( (col, row) )

            # 256色模式中，r:g:b = 3:3:2 bits
            r >>= 5; g >>= 5; b >>=6

            # 搜索最匹配图片
            if alpha == 0 :
                # 如果png图片在此位置的透明度是0，画个空气（寂寞）
                materialID, subIndex = (block.AIR.id, 0)
            else:
                materialID, subIndex = dictColor256ToMaterail[ (r, g, b) ]
            

            # 平着画，脚下-100的位置，玩家应该站在100+的高度
            mc.setBlock(x-col + imgW/2, y-100, z + (imgH/2-row), materialID, subIndex)
            # 竖着画，前方30格位置
            # mc.setBlock(x+30, y - row + imgH, z + col - imgW/2, materialID, subIndex)
        time.sleep(0.05)


##########################################################################
# 入口
if __name__ == '__main__':
    print("示例代码，简洁起见，必须使用png格式图片")
    time.sleep(5)
    init()
    
    img = Image.open("miku.png")
    drawFrame(img)
    print("绘制完成，等待mc刷新...")

            

