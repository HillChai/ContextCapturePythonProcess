import ccmasterkernel
import sys
import os
import shutil

SENSORSIZE_MM = 5.146
FOCALLENGTH_MM = 3.99
photosDirPath = 'C:/Users/chaic/Desktop/Plan/3DataSets/14-13-39-51/pic'
inputFilePath = 'C:/Users/chaic/Desktop/Plan/3DataSets/14-13-39-51/attitudes.txt'
projectDirPath = 'C:/Users/chaic/Desktop/Plan/14SDKUtilization/myProject'
projectName = os.path.basename(projectDirPath)

if os.path.exists(projectDirPath):
    shutil.rmtree(projectDirPath)

project = ccmasterkernel.Project()
project.setName(projectName)
project.setProjectFilePath(os.path.join(projectDirPath, projectName))

# err = project.writeToFile()
# if not err.isNone():
#     print(err.message)
#     sys.exit(0)

print('Project %s successfully created.' % projectName)
print('')

# create block
block = ccmasterkernel.Block(project)
block.setPositioningLevel(ccmasterkernel.PositioningLevel.PositioningLevel_absolute)
project.addBlock(block)

photogroups = block.getPhotogroups()
photogroups.addPhotogroup(ccmasterkernel.Photogroup())
photogroup = photogroups.getPhotogroup(photogroups.getNumPhotogroups() - 1)

# parse input txt file
firstPhoto = True

srs_manager = project.getProjectSRSManager()
srs_cp_id = srs_manager.getOrCreateProjectSRSId("Local:0", "Local coordinate system (arbitrary unit)")

with open(inputFilePath, 'r') as f:
    for line in f.readlines():
        content = line.split(',')

        imageFilePath = content[0]
        photo = ccmasterkernel.Photo(imageFilePath)
        photo.pose.center = ccmasterkernel.Point3d(float(content[1]), float(content[2]), float(content[3]))
        photo.poseMetadata.center = ccmasterkernel.Point3d(float(content[1]), float(content[2]), float(content[3]))

        # 欧拉角转旋转矩阵这一步是对的，但是XRightYUp这里改不过来，不要旋转矩阵，就可以变成自己的坐标系。
        # 自己写XML
        # 想办法把Matrix3里的后六个向量变为相反数 bingo
        rotMat = ccmasterkernel.omegaPhiKappaToMatrix(float(content[4]), float(content[5]), float(content[6]))

        for i in range(1,3):
            for j in range(3):
                rotMat.setElement(i,j, -rotMat.getElement(i, j))
                # print(rotMat.getElement(i, j))

        photo.pose.rotation = rotMat
        photo.poseMetadata.rotation = rotMat
        # Invalid SRS poseMetadata solution
        photo.poseMetadata.srsId = srs_cp_id

        if firstPhoto:
            firstPhoto = False
            photogroup.setupFromPhoto(photo)
            photogroup.sensorSize_mm = SENSORSIZE_MM
            photogroup.focalLength_mm = FOCALLENGTH_MM

        photogroup.addPhoto(photo)



block.setChanged()


# export 用于核对xml信息
# exportOptions = ccmasterkernel.BlockExportOptions()
# exportOptions.cameraOrientation = ccmasterkernel.bindings.CameraOrientation.XRightYUp
# extractedBlock = project.getBlock(project.getNumBlocks() - 1)
# blockExportedErr = extractedBlock.exportToBlocksExchangeXML(os.path.join(projectDirPath,'block-extract.xml'), exportOptions)

# if not blockExportedErr.isNone():
#     print('Failed to export block extract')
#     sys.exit(0)

# --------------------------------------------------------------------  导出时改为XRightYUp，导入时还是不行
# import block
# --------------------------------------------------------------------
# inputBlockFilePath = os.path.join(projectDirPath,'block-extract.xml')
# inputBlockFilePath = 'C:/Users/chaic/Desktop/Plan/14SDKUtilization/YUp.xml'
# importErr = project.importBlocks(inputBlockFilePath)
# if not importErr.isNone():
#     print('Failed to import block')
#     print(importErr.message)
#     sys.exit(0)
#
# importedBlock = project.getBlock(project.getNumBlocks() - 1)
# --------------------------------------------------------------------
# unload imported block
# --------------------------------------------------------------------
# importedBlock.unload()

err = project.writeToFile()
if not err.isNone():
    print(err.message)
    sys.exit(0)