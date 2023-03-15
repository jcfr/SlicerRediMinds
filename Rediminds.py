import logging
import os
import urllib.parse
import vtk
import qt
import slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
import platform
import shutil

#
# Rediminds
#

segtoken = None


class Rediminds(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        # TODO: make this more human readable by adding spaces
        self.parent.title = "Rediminds"
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = ["Rediminds"]
        # TODO: add here list of module names that this module requires
        self.parent.dependencies = []
        # TODO: replace with "Firstname Lastname (Organization)"
        self.parent.contributors = [
            "K Mordhwaj (Inzint)", "Andras Lasso (PerkLab)", "ASH"]
        # TODO: update with short description of the module and a link to online module documentation
        self.parent.helpText = """
This is a scripted loadable module bundled in Rediminds extension.The purpose of this module is to process the various images and segmentations and send back to the backend server.
"""
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = """
This file was developed by K Mordhwaj, Inzint on behalf of Rediminds. In first part, taken reference from LoadRemote.py file of SlicerSandbox
"""

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)

        # Initilize self.sampleDataLogic. At this point, Slicer modules are not initialized yet, so we cannot instantiate the logic yet.
        self.sampleDataLogic = None

        slicer.app.connect("urlReceived(QString)", self.onURLReceived)

    def onURLReceived(self, urlString):
        global segtoken
        decodedUrlString = urllib.parse.unquote(urlString)

        # Split the urlString to extract segmentation and image parts
        segimgPart = decodedUrlString.split("segmentation=").pop()
        segImgArr = segimgPart.split("&image=")
        imgPart = segImgArr.pop()
        segPart = segImgArr[0]

        segPartBack = segPart.split("?").pop()
        segPartBackArr = segPartBack.split("&")
        segAlg = segPartBackArr[0]
        segCont = segPartBackArr[1]
        segCred = segPartBackArr[2]
        segDate = segPartBackArr[3]
        segExpire = segPartBackArr[4]
        segToken = segPartBackArr[5]
        # self.token = segToken
        segTokenMod = segToken.split('=').pop()
        segtoken = segTokenMod
        segHeader = segPartBackArr[7]
        segGet = segPartBackArr[8]

        imgPartArr = imgPart.split("&")
        imgBase = imgPartArr[0]
        imgSign = imgPartArr[1]

        imgUrl = f"{imgBase}?{segAlg}&{segCont}&{segCred}&{segDate}&{segExpire}&{segToken}&{imgSign}&{segHeader}&{segGet}"

        encodedSegPart = urllib.parse.quote(segPart)
        encodedImgPart = urllib.parse.quote(imgUrl)

        mainUrl = f"slicer://viewer/?segmentation={encodedSegPart}&image={encodedImgPart}"

        # Check if we understand this URL
        url = qt.QUrl(mainUrl)
        if url.authority().lower() != "viewer":
            return
        query = qt.QUrlQuery(url)

        # Get list of files to load
        filesToOpen = []
        for key, value in query.queryItems(qt.QUrl.FullyDecoded):
            if key == "download":
                fileType = None
            elif key == "image" or key == "volume":
                fileType = "VolumeFile"
            elif key == "segmentation":
                fileType = "SegmentationFile"
            else:
                continue
            downloadUrl = qt.QUrl(value)

            # Get the node name from URL
            nodeName, ext = os.path.splitext(
                os.path.basename(downloadUrl.path()))
            # Generate random filename to avoid reusing/overwriting older downloaded files that may have the same name
            import uuid
            fileName = f"{nodeName}-{uuid.uuid4().hex}{ext}"
            info = {"downloadUrl": downloadUrl, "nodeName": nodeName,
                    "fileName": fileName, "fileType": fileType}
            filesToOpen.append(info)

        if not filesToOpen:
            return

        # Parse additional options
        queryMap = {}
        for key, value in query.queryItems(qt.QUrl.FullyDecoded):
            queryMap[key] = value

        show3d = False
        if "show3d" in queryMap:
            print("Show 3d")
            show3d = slicer.util.toBool(queryMap["show3d"])

        # Ensure sampleData logic is created
        if not self.sampleDataLogic:
            import SampleData
            self.sampleDataLogic = SampleData.SampleDataLogic()

        for info in filesToOpen:
            downloadUrlString = info["downloadUrl"].toString()
            try:
                self.progressWindow = slicer.util.createProgressDialog()
                self.sampleDataLogic.logMessage = self.reportProgress

                loadedNodes = self.sampleDataLogic.downloadFromURL(
                    nodeNames=info["nodeName"], fileNames=info["fileName"], uris=downloadUrlString, loadFileTypes=info["fileType"])

                filePathBefore = slicer.app.cachePath + "/" + info["fileName"]

                os.remove(filePathBefore)

                if show3d:
                    for loadedNode in loadedNodes:
                        if type(loadedNode) == slicer.vtkMRMLSegmentationNode:
                            # Show segmentation in 3D
                            loadedNode.CreateClosedSurfaceRepresentation()

            finally:
                # shNode = slicer.mrmlScene.GetSubjectHierarchyNode()
                # exportFolderItemId = shNode.CreateFolderItem(
                #     shNode.GetSceneItemID(), "Segments")
                # slicer.modules.segmentations.logic().ExportAllSegmentsToModels(
                #     self.segmentationNode, exportFolderItemId)
                self.progressWindow.close()

        if show3d:
            self.center3dViews()
            self.showSliceViewsIn3d()

    def reportProgress(self, message, logLevel=None):
        # Print progress in the console
        print(f"Loading... {self.sampleDataLogic.downloadPercent}%")
        # Abort download if cancel is clicked in progress bar
        if self.progressWindow.wasCanceled:
            raise Exception("download aborted")
        # Update progress window
        self.progressWindow.show()
        self.progressWindow.activateWindow()
        self.progressWindow.setValue(int(self.sampleDataLogic.downloadPercent))
        self.progressWindow.setLabelText("Downloading...")
        # Process events to allow screen to refresh
        slicer.app.processEvents()

    def center3dViews(self):
        layoutManager = slicer.app.layoutManager()
        for threeDViewIndex in range(layoutManager.threeDViewCount):
            threeDWidget = layoutManager.threeDWidget(0)
            threeDView = threeDWidget.threeDView()
            threeDView.resetFocalPoint()

    def showSliceViewsIn3d(self):
        layoutManager = slicer.app.layoutManager()
        for sliceViewName in layoutManager.sliceViewNames():
            controller = layoutManager.sliceWidget(
                sliceViewName).sliceController()
            controller.setSliceVisible(True)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """
    Add data sets to Sample Data module.
    """
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData
    iconsPath = os.path.join(os.path.dirname(__file__), 'Resources/Icons')

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # Rediminds1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='Rediminds',
        sampleName='Rediminds1',
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, 'Rediminds1.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames='Rediminds1.nrrd',
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums='SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95',
        # This node name will be used when the data set is loaded
        nodeNames='Rediminds1'
    )

    # Rediminds2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category='Rediminds',
        sampleName='Rediminds2',
        thumbnailFileName=os.path.join(iconsPath, 'Rediminds2.png'),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames='Rediminds2.nrrd',
        checksums='SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97',
        # This node name will be used when the data set is loaded
        nodeNames='Rediminds2'
    )


#
# RedimindsWidget
#

class RedimindsWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.__init__(self, parent)
        # needed for parameter node observation
        VTKObservationMixin.__init__(self)
        self.logic = None
        self._parameterNode = None
        self._updatingGUIFromParameterNode = False

        # # # Create instance of Rediminds class
        self.segmentationNode = None
        self.sampleDataLogic = None

    def setup(self):
        """
        Called when the user opens the module the first time and the widget is initialized.
        """
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath('UI/Rediminds.ui'))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = RedimindsLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(
            slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene,
                         slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        self.ui.inputSelector.connect(
            "currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)

        global segtoken
        segToken = segtoken

        # Buttons
        self.ui.sendToBackendButton.connect(
            'clicked(bool)', lambda: self.sendToBackendButton(segToken))

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self):
        """
        Called when the application closes and the module widget is destroyed.
        """
        self.removeObservers()

    def enter(self):
        """
        Called each time the user opens this module.
        """
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self):
        """
        Called each time the user opens a different module.
        """
        # Do not react to parameter node changes (GUI wlil be updated when the user enters into the module)
        self.removeObserver(
            self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

    def onSceneStartClose(self, caller, event):
        """
        Called just before the scene is closed.
        """
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event):
        """
        Called just after the scene is closed.
        """
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self):
        """
        Ensure parameter node exists and observed.
        """
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.GetNodeReference("InputVolume"):
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass(
                "vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.SetNodeReferenceID(
                    "InputVolume", firstVolumeNode.GetID())

    def setParameterNode(self, inputParameterNode):
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if inputParameterNode:
            self.logic.setDefaultParameters(inputParameterNode)

        # Unobserve previously selected parameter node and add an observer to the newly selected.
        # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
        # those are reflected immediately in the GUI.
        if self._parameterNode is not None:
            self.removeObserver(
                self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
        self._parameterNode = inputParameterNode
        if self._parameterNode is not None:
            self.addObserver(
                self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)

        # Initial GUI update
        self.updateGUIFromParameterNode()

    def updateGUIFromParameterNode(self, caller=None, event=None):
        """
        This method is called whenever parameter node is changed.
        The module GUI is updated to show the current state of the parameter node.
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Make sure GUI changes do not call updateParameterNodeFromGUI (it could cause infinite loop)
        self._updatingGUIFromParameterNode = True

        # Update node selectors and sliders
        self.ui.inputSelector.setCurrentNode(
            self._parameterNode.GetNodeReference("InputVolume"))

        # All the GUI updates are done
        self._updatingGUIFromParameterNode = False

    def updateParameterNodeFromGUI(self, caller=None, event=None):
        """
        This method is called when the user makes any change in the GUI.
        The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
        """

        if self._parameterNode is None or self._updatingGUIFromParameterNode:
            return

        # Modify all properties in a single batch
        wasModified = self._parameterNode.StartModify()

        self._parameterNode.SetNodeReferenceID(
            "InputVolume", self.ui.inputSelector.currentNodeID)

        self._parameterNode.EndModify(wasModified)

    def sendToBackendButton(self, segtoken):

        progressDialog = slicer.util.createProgressDialog(
            parent=self.parent, value=0, maximum=100, labelText="Please wait...", windowTitle="Syncing data with backend")

        # Start the progress dialog
        progressDialog.show()

        self.segmentationNode = slicer.mrmlScene.GetNodeByID(
            "vtkMRMLSegmentationNode1")

        # Create a folder in the user's home directory if it doesn't exist
        if platform.system() == 'Windows':
            folderPath = os.path.join(
                os.environ['USERPROFILE'], 'SlicerSTL')
        else:
            folderPath = os.path.join(
                os.path.expanduser('~'), 'SlicerSTL')
        if not os.path.exists(folderPath):
            os.makedirs(folderPath)

        # set the destination folder to the newly created folder
        destinationFolder = folderPath

        # export all segments to STL files
        slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(
            destinationFolder, self.segmentationNode)

        zipFileToS3 = shutil.make_archive(
            destinationFolder, 'zip', destinationFolder)
        name = self.segmentationNode.GetName()
        nameString = str(name)
        fileKey = nameString[:-4]
        fileKeyZip = fileKey + ".zip"

        # Generate a presigned S3 POST URL
        object_name = fileKeyZip
        bucket_name = 'gtf-development-slicer-output'
        fields = {"key": object_name}
        conditions = [{"acl": "private"}]
        token = segtoken

        response = self.create_presigned_post(
            bucket_name, object_name)
        if response is None:
            exit(1)

        needToInstallRequest = False
        try:
            import requests
        except ModuleNotFoundError as e:
            needToInstallRequest = True

        if needToInstallRequest:
            slicer.util.pip_install("requests")

        # Upload file to S3 using the presigned URL and custom header
        with open(zipFileToS3, 'rb') as f:
            files = {'file': (zipFileToS3, f)}
            # Add custom header to the POST request
            headers = {'x-amz-meta-token': token}
            http_response = requests.post(
                response['url'], data=response['fields'], files=files
                # , headers=headers
            )

        # If successful, returns HTTP status code 204
        logging.info(
            f'File upload HTTP status code: {http_response.status_code}')

        shutil.rmtree(destinationFolder)
        os.remove(zipFileToS3)

        progressDialog.close()

    def create_presigned_post(self, bucket_name, object_name):
        # Generate a presigned S3 POST URL
        needToInstallBoto3 = False
        try:
            import boto3
        except ModuleNotFoundError as e:
            needToInstallBoto3 = True

        if needToInstallBoto3:
            slicer.util.pip_install("boto3")

        s3_client = boto3.client('s3')

        from botocore.exceptions import ClientError

        try:
            # Add custom header to the conditions list
            # conditions = conditions or []
            # conditions.append({"x-amz-meta-token": token})
            response = s3_client.generate_presigned_post(bucket_name,
                                                         object_name,
                                                         # Fields=fields,
                                                         # Conditions=conditions,
                                                         ExpiresIn=3600)
        except ClientError as e:
            logging.error(e)
            return None

        # The response contains the presigned URL and required fields
        return response

#
# RedimindsLogic
#


class RedimindsLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self):
        """
        Called when the logic class is instantiated. Can be used for initializing member variables.
        """
        ScriptedLoadableModuleLogic.__init__(self)

    def setDefaultParameters(self, parameterNode):
        """
        Initialize parameter node with default settings.
        """
        if not parameterNode.GetParameter("Threshold"):
            parameterNode.SetParameter("Threshold", "100.0")
        if not parameterNode.GetParameter("Invert"):
            parameterNode.SetParameter("Invert", "false")

    def process(self, inputVolume, outputVolume, imageThreshold, invert=False, showResult=True):
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time
        startTime = time.time()
        logging.info('Processing started')

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            'InputVolume': inputVolume.GetID(),
            'OutputVolume': outputVolume.GetID(),
            'ThresholdValue': imageThreshold,
            'ThresholdType': 'Above' if invert else 'Below'
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None,
                                 cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(
            f'Processing completed in {stopTime-startTime:.2f} seconds')


#
# RedimindsTest
#

class RedimindsTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
        """
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here.
        """
        self.setUp()
        self.test_Rediminds1()

    def test_Rediminds1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData
        registerSampleData()
        inputVolume = SampleData.downloadSample('Rediminds1')
        self.delayDisplay('Loaded test data set')

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass(
            "vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = RedimindsLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay('Test passed')
