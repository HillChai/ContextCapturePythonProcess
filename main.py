from ContextCapture import ContextCapture

SENSORSIZE_MM = 5.146
FOCALLENGTH_MM = 3.99
photosDirPath = 'C:/Users/chaic/Desktop/Plan/3DataSets/14-13-39-51/pic'
attitudesPath = 'C:/Users/chaic/Desktop/Plan/3DataSets/14-13-39-51/attitudes.txt'
projectDirPath = 'C:/Users/chaic/Desktop/Plan/14SDKUtilization/myProject'

# Remember starting the Engine first

#Project Creation
instance = ContextCapture()
instance.createProject(SENSORSIZE_MM, FOCALLENGTH_MM, photosDirPath, attitudesPath, projectDirPath)
#Block for importing data
instance.createBlock()
# AT
instance.createAT()
# Reconstruction
instance.Reconstruction()












