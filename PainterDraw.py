import json
import os

path = "C:/Users/chaic/Desktop/Plan/3DataSets/14-13-39-51/"
jsonName = "14-13-39-51.json"
prefix = "C:/Users/chaic/Desktop/Plan/3DataSets/14-13-39-51/pic/"


class processor:
    def __init__(self, path, jsonName):
        self.data = []
        self.n = 0
        self.id = []
        self.position = []
        self.eulerAngle = []
        with open(path + jsonName, encoding="utf-8") as f:
            # content = f.read()
            # a = json.loads(content)    #字符串转python任何类型，此处为列表
            self.data = json.load(f)
            self.n = len(self.data)

    def getPosition(self):
        self.position = []
        for i in range(self.n):
            self.position.append([(self.data[i]["position"][j]) for j in range(3)])
        return self.position

    def geteulerAngle(self):
        self.eulerAngle = []
        for i in range(self.n):
            self.eulerAngle.append(self.data[i]["eulerAngle"])
        return self.eulerAngle

    def getID(self):
        self.id = []
        for i in range(self.n):
            self.id.append(self.data[i]["id"])
        return self.id

    def checkNoPhoto(self):
        cnt_success = 0
        for name in self.id:
            if os.access(self.path + name + ".jpg", os.F_OK):  # F_OK, R_OK, W_OK, X_OK
                cnt_success += 1
        print("cnt_total, cnt_success: ", self.n, cnt_success)


target = processor(path=path, jsonName=jsonName)

ARKitPosition = target.getPosition()
ARKitEuler = target.geteulerAngle()
SnapId = target.getID()
# print("SnapId: ", SnapId)

PicLocation = []

for i in range(len(ARKitPosition)):
    PicLocation.append(prefix + SnapId[i] + ".jpg")
#     print(os.path.exists(PicLocation[i]))
print(len(ARKitPosition), len(ARKitEuler), len(PicLocation))

txtName = path+"attitudes.txt"
if os.path.exists(txtName):
    os.remove(txtName)

with open(txtName, 'w') as f:
    for i in range(0, len(ARKitPosition)):
        content = PicLocation[i] + "," \
                  + str(ARKitPosition[i][0]) + "," \
                  + str(ARKitPosition[i][1]) + "," \
                  + str(ARKitPosition[i][2]) + "," \
                  + str(ARKitEuler[i][0]) + "," \
                  + str(ARKitEuler[i][1]) + "," \
                  + str(ARKitEuler[i][2]) + "\n"

        f.write(content)


import matplotlib.pyplot as plt
import numpy as np
class painter:
    def __init__(self, position):
        self.n = len(position)
        self.x = []
        self.y = []
        self.z = []
        for i in range(self.n):
            self.x.append(position[i][0])
            self.y.append(position[i][1])
            self.z.append(position[i][2])

    def draw2D(self,title):
        f, ax = plt.subplots(2,2)
        f.suptitle(title)

        ax[0][0].plot([i for i in range(self.n)], self.x)
        # plt.ylim(-0.5, 1)
        ax[0][0].set_title("X-axis")

        ax[0][1].plot([i for i in range(self.n)], self.y)
        # plt.ylim(-0.5, 1)
        ax[0][1].set_title("Y-axis")

        ax[1][0].plot([i for i in range(self.n)], self.z)
        # plt.ylim(-0.5, 1)
        # ax[1][0].set_title("Z-axis")

        plt.show()
    def draw3D(self, title):
        fig = plt.figure(figsize=(8, 6))
        # 创建渐变色映射
        colors = plt.cm.viridis(np.linspace(0, 1, self.n))
        ax4 = fig.add_subplot(111, projection='3d')
        ax4.plot(self.x, self.y, self.z, color='darkblue')
        scatter = ax4.scatter(self.x, self.y, self.z, c=colors, marker='o')
        ax4.set_xlabel('X')
        # ax4.set_xlim([-0.5,2])
        ax4.set_ylabel('Y')
        # ax4.set_ylim([-0.5,2])
        ax4.set_zlabel('Z')
        # ax4.set_zlim([-0.5,2])
        colorbar = plt.colorbar(scatter, ax=ax4, label='Color', shrink=0.7)
        plt.show()

instance = painter(ARKitPosition)
instance.draw2D("test2D")
instance.draw3D("test3D")