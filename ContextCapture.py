import ccmasterkernel
import sys
import os
import shutil
import time

class ContextCapture:
    def __init__(self):
        self.SENSORSIZE_MM = 0.0
        self.FOCALLENGTH_MM = 0.0
        self.photosDirPath = ""
        self.attitudesPath = ""
        self.projectDirPath = ""
        self.projectName = ""
        self.project = ccmasterkernel.Project()
        self.block = ccmasterkernel.Block(self.project)
        self.blockAT = ccmasterkernel.Block(self.project)

    def createProject(self, SENSORSIZE_MM, FOCALLENGTH_MM, photosDirPath, attitudesPath, projectDirPath):
        self.SENSORSIZE_MM = SENSORSIZE_MM  # 传感器
        self.FOCALLENGTH_MM = FOCALLENGTH_MM  # 焦距
        self.photosDirPath = photosDirPath  # 照片文件夹
        self.attitudesPath = attitudesPath  # 位姿txt文件
        self.projectDirPath = projectDirPath  # cc项目创建地址
        self.projectName = os.path.basename(projectDirPath)  # cc工程名称

        if os.path.exists(projectDirPath):
            shutil.rmtree(projectDirPath)

        self.project.setName(self.projectName)
        self.project.setProjectFilePath(os.path.join(projectDirPath, self.projectName))

        print('Project %s successfully created.' % self.projectName)

    def createBlock(self):

        self.block.setPositioningLevel(ccmasterkernel.PositioningLevel.PositioningLevel_absolute)
        self.project.addBlock(self.block)

        photogroups = self.block.getPhotogroups()
        photogroups.addPhotogroup(ccmasterkernel.Photogroup())
        photogroup = photogroups.getPhotogroup(photogroups.getNumPhotogroups() - 1)

        # parse input txt file
        firstPhoto = True

        srs_manager = self.project.getProjectSRSManager()
        srs_cp_id = srs_manager.getOrCreateProjectSRSId("Local:0", "Local coordinate system (arbitrary unit)")

        with open(self.attitudesPath, 'r') as f:
            for line in f.readlines():
                content = line.split(',')

                imageFilePath = content[0]
                photo = ccmasterkernel.Photo(imageFilePath)
                photo.pose.center = ccmasterkernel.Point3d(float(content[1]), float(content[2]), float(content[3]))
                photo.poseMetadata.center = ccmasterkernel.Point3d(float(content[1]), float(content[2]),
                                                                   float(content[3]))

                # 欧拉角转旋转矩阵这一步是对的，但是XRightYUp这里改不过来，不要旋转矩阵，就可以变成自己的坐标系。
                # 自己写XML
                # 想办法把Matrix3里的后六个向量变为相反数 bingo
                rotMat = ccmasterkernel.omegaPhiKappaToMatrix(float(content[4]), float(content[5]), float(content[6]))

                for i in range(1, 3):
                    for j in range(3):
                        rotMat.setElement(i, j, -rotMat.getElement(i, j))
                        # print(rotMat.getElement(i, j))

                photo.pose.rotation = rotMat
                photo.poseMetadata.rotation = rotMat
                # Invalid SRS poseMetadata solution
                photo.poseMetadata.srsId = srs_cp_id

                if firstPhoto:
                    firstPhoto = False
                    photogroup.setupFromPhoto(photo)
                    photogroup.sensorSize_mm = self.SENSORSIZE_MM
                    photogroup.focalLength_mm = self.FOCALLENGTH_MM

                photogroup.addPhoto(photo)

        self.block.setChanged()

        if not self.block.isReadyForAT():
            if self.block.reachedLicenseLimit():
                print('Error: License limit reached.')
            if self.block.getPhotogroups().getNumPhotos() < 3:
                print('Error: Not enough photos.')
            else:
                print('Error: Missing focal lengths and sensor sizes.')
            sys.exit(0)

    def createAT(self):
        self.project.addBlock(self.blockAT)
        self.blockAT.setBlockTemplate(ccmasterkernel.BlockTemplate.Template_adjusted, self.block)

        err = self.project.writeToFile()
        if not err.isNone():
            print(err.message)
            sys.exit(0)

        at_settings = self.blockAT.getAT().getSettings()
        at_settings.keyPointsDensity = ccmasterkernel.KeyPointsDensity.KeyPointsDensity_high
        # at_settings.splatsPreprocessing = ccmasterkernel.SplatsPreprocessing.SplatsPreprocessing_None
        if not self.blockAT.getAT().setSettings(at_settings):
            print("Error: Failed to set settings for aerotriangulation")
            sys.exit(0)
        atSubmitError = self.blockAT.getAT().submitProcessing()

        if not atSubmitError.isNone():
            print('Error: Failed to submit aerotriangulation.')
            print(atSubmitError.message)
            sys.exit(0)

        print('The aerotriangulation job has been submitted and is waiting to be processed...')

        iPreviousProgress = 0
        iProgress = 0
        previousJobStatus = ccmasterkernel.JobStatus.Job_unknown
        jobStatus = ccmasterkernel.JobStatus.Job_unknown

        while True:
            jobStatus = self.blockAT.getAT().getJobStatus()

            if jobStatus != previousJobStatus:
                print(ccmasterkernel.jobStatusAsString(jobStatus))

            if jobStatus == ccmasterkernel.JobStatus.Job_failed or \
                    jobStatus == ccmasterkernel.JobStatus.Job_cancelled or \
                    jobStatus == ccmasterkernel.JobStatus.Job_completed:
                break

            if iProgress != iPreviousProgress:
                print('%s%% - %s' % (iProgress, self.blockAT.getAT().getJobMessage()))

            iPreviousProgress = iProgress
            iProgress = self.blockAT.getAT().getJobProgress()
            time.sleep(1)
            self.blockAT.getAT().updateJobStatus()
            previousJobStatus = jobStatus

        if jobStatus != ccmasterkernel.JobStatus.Job_completed:
            print("Error: Incomplete aerotriangulation.")

            if self.blockAT.getAT().getJobMessage() != '':
                print(self.blockAT.getAT().getJobMessage())

        print('Aerotriangulation job finished.')

        if not self.blockAT.canGenerateQualityReport():
            print("Error: BlockAT can't generate Quality report")
            sys.exit(0)

        if not self.blockAT.generateQualityReport(True):
            print("Error: failed to generate Quality report")
            sys.exit(0)

        print("AT report available at", self.blockAT.getQualityReportPath())

        if not self.blockAT.isReadyForReconstruction():
            print('Error: Incomplete photos. Cannot create reconstruction.')
            sys.exit(0)

        print('Ready for reconstruction.')

        if self.blockAT.getPhotogroups().getNumPhotosWithCompletePose_byComponent(
                1) < self.blockAT.getPhotogroups().getNumPhotos():
            print('Warning: incomplete photos. %s/%s photo(s) cannot be used for reconstruction.' % (
                self.blockAT.getPhotogroups().getNumPhotos() - self.blockAT.getPhotogroups().getNumPhotosWithCompletePose_byComponent(
                    1),
                self.blockAT.getPhotogroups().getNumPhotos()));

    def Reconstruction(self):
        reconstruction = ccmasterkernel.Reconstruction(self.blockAT)
        self.blockAT.addReconstruction(reconstruction)

        if reconstruction.getNumInternalTiles() == 0:
            print('Error: Failed to create reconstruction layout.')
            sys.exit(0)

        print('Reconstruction item created.')

        # -------------------------------------------------------------------
        # Production
        # -------------------------------------------------------------------
        production = ccmasterkernel.Production(reconstruction)
        reconstruction.addProduction(production)

        production.setDriverName('3MX')
        production.setDestination(os.path.join(self.project.getProductionsDirPath(), production.getName()))

        driverOptions = production.getDriverOptions()
        driverOptions.put_bool('TextureEnabled', True)
        driverOptions.put_int('TextureCompressionQuality', 80)
        driverOptions.writeXML(os.path.join(self.project.getProductionsDirPath(), "options.xml"))

        production.setDriverOptions(driverOptions)

        print('Production item created.')

        productionSubmitError = production.submitProcessing()

        if not productionSubmitError.isNone():
            print('Error: Failed to submit production.')
            print(productionSubmitError.message)
            sys.exit(0)

        print('The production job has been submitted and is waiting to be processed...')

        iPreviousProgress = 0
        iProgress = 0
        previousJobStatus = ccmasterkernel.JobStatus.Job_unknown

        while True:
            jobStatus = production.getJobStatus()

            if jobStatus != previousJobStatus:
                print(ccmasterkernel.jobStatusAsString(jobStatus))

            if jobStatus == ccmasterkernel.JobStatus.Job_failed or \
                    jobStatus == ccmasterkernel.JobStatus.Job_cancelled or \
                    jobStatus == ccmasterkernel.JobStatus.Job_completed:
                break

            if iProgress != iPreviousProgress:
                print('%s%% - %s' % (iProgress, production.getJobMessage()))

            iPreviousProgress = iProgress
            iProgress = production.getJobProgress()
            time.sleep(1)
            production.updateJobStatus()
            previousJobStatus = jobStatus

        print('')

        if jobStatus != ccmasterkernel.JobStatus.Job_completed:
            print('Error: Incomplete production.')

            if production.getJobMessage() != '':
                print(production.getJobMessage())

        print('Production job finished.')
        print('Output directory: %s' % production.getDestination())

    def writeProject(self):
        err = self.project.writeToFile()
        if not err.isNone():
            print(err.message)
            sys.exit(0)


# SENSORSIZE_MM = 5.146
# FOCALLENGTH_MM = 3.99
# photosDirPath = 'C:/Users/chaic/Desktop/Plan/3DataSets/14-13-39-51/pic'
# attitudesPath = 'C:/Users/chaic/Desktop/Plan/3DataSets/14-13-39-51/attitudes.txt'
# projectDirPath = 'C:/Users/chaic/Desktop/Plan/14SDKUtilization/myProject'
#
# instance = ContextCapture()
# instance.createProject(SENSORSIZE_MM, FOCALLENGTH_MM, photosDirPath, attitudesPath, projectDirPath)
# instance.createBlock()
# instance.writeProject()