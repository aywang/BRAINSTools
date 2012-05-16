#!/usr/bin/env python

from nipype.interfaces.base import CommandLine, CommandLineInputSpec, TraitedSpec, File, Directory
from nipype.interfaces.base import traits, isdefined, BaseInterface
from nipype.interfaces.utility import Merge, Split, Function, Rename, IdentityInterface
import nipype.interfaces.io as nio   # Data i/o
import nipype.pipeline.engine as pe  # pypeline engine

from BRAINSTools.RF12BRAINSCutWrapper import RF12BRAINSCutWrapper

"""
    from WorkupT1T2BRAINSCutSegmentation import CreateBRAINSCutSegmentationWorkflow
    myLocalcutWF= CreateBRAINSCutSegmentationWorkflow("999999_PersistanceCheckingWorkflow")
    cutWF.connect(SplitAvgBABC,'avgBABCT1',myLocalcutWF,'fixedVolume')
    cutWF.connect(BABC,'outputLabels',myLocalcutWF,'fixedBinaryVolume')
    cutWF.connect(BAtlas,'template_t1',myLocalcutWF,'movingVolume')
    cutWF.connect(BAtlas,'template_brain',myLocalcutWF,'movingBinaryVolume')
    cutWF.connect(BLI,'outputTransformFilename',myLocalcutWF,'initialTransform')
"""
def CreateBRAINSCutWorkflow(WFname,CLUSTER_QUEUE,atlasObject):
    cutWF= pe.Workflow(name=WFname)

    inputsSpec = pe.Node(interface=IdentityInterface(fields=['T1Volume','T2Volume',
        'atlasToSubjectTransform']), name='InputSpec' )

    """
    Gradient Anistropic Diffusion images for BRAINSCut
    """
    GADT1=pe.Node(interface=GradientAnisotropicDiffusionImageFilter(),name="GADT1")
    GADT1.inputs.timeStep = 0.025
    GADT1.inputs.conductance = 1
    GADT1.inputs.numberOfIterations = 5
    GADT1.inputs.outputVolume = "GADT1.nii.gz"

    cutWF.connect(inputsSpec,'T1Volume',GADT1,'inputVolume')

    GADT2=pe.Node(interface=GradientAnisotropicDiffusionImageFilter(),name="GADT2")
    GADT2.inputs.timeStep = 0.025
    GADT2.inputs.conductance = 1
    GADT2.inputs.numberOfIterations = 5
    GADT2.inputs.outputVolume = "GADT2.nii.gz"
    cutWF.connect(inputsSpec,'T2Volume',GADT2,'inputVolume')

    """
    Sum the gradient images for BRAINSCut
    """
    SGI=pe.Node(interface=GenerateSummedGradientImage(),name="SGI")
    SGI.inputs.outputFileName = "SummedGradImage.nii.gz"

    cutWF.connect(GADT1,'outputVolume',SGI,'inputVolume1')
    cutWF.connect(GADT2,'outputVolume',SGI,'inputVolume2')

    """
    BRAINSCut
    """
    RF12BC = pe.Node(interface=RF12BRAINSCutWrapper(),name="RF12_BRAINSCut")
    RF12BC.inputs.trainingVectorFilename = "dummy.txt"

    cutWF.connect(inputSpec,'T1Volume',RF12BC,'inputSubjectT1Filename')
    cutWF.connect(inputSpec,'T2Volume',RF12BC,'inputSubjectT2Filename')
    cutWF.connect(SGI,'outputVolume',RF12BC,'inputSubjectSGFilename')
    cutWF.connect(atlasObject,'template_t1',RF12BC,'inputTemplateT1')
    cutWF.connect(atlasObject,'spatialImages/rho',RF12BC,'inputTemplateRhoFilename')
    cutWF.connect(atlasObject,'spatialImages/phi',RF12BC,'inputTemplatePhiFilename')
    cutWF.connect(atlasObject,'spatialImages/theta',RF12BC,'inputTemplateThetaFilename')


    cutWF.connect(atlasObject,'probabilityMaps/l_accumben_ProbabilityMap',RF12BC,'probabilityMapsLeftAccumben')
    cutWF.connect(atlasObject,'probabilityMaps/r_accumben_ProbabilityMap',RF12BC,'probabilityMapsRightAccumben')
    cutWF.connect(atlasObject,'probabilityMaps/l_caudate_ProbabilityMap',RF12BC,'probabilityMapsLeftCaudate')
    cutWF.connect(atlasObject,'probabilityMaps/r_caudate_ProbabilityMap',RF12BC,'probabilityMapsRightCaudate')
    cutWF.connect(atlasObject,'probabilityMaps/l_globus_ProbabilityMap',RF12BC,'probabilityMapsLeftGlobus')
    cutWF.connect(atlasObject,'probabilityMaps/r_globus_ProbabilityMap',RF12BC,'probabilityMapsRightGlobus')
    cutWF.connect(atlasObject,'probabilityMaps/l_hippocampus_ProbabilityMap',RF12BC,'probabilityMapsLeftHippocampus')
    cutWF.connect(atlasObject,'probabilityMaps/r_hippocampus_ProbabilityMap',RF12BC,'probabilityMapsRightHippocampus')
    cutWF.connect(atlasObject,'probabilityMaps/l_putamen_ProbabilityMap',RF12BC,'probabilityMapsLeftPutamen')
    cutWF.connect(atlasObject,'probabilityMaps/r_putamen_ProbabilityMap',RF12BC,'probabilityMapsRightPutamen')
    cutWF.connect(atlasObject,'probabilityMaps/l_thalamus_ProbabilityMap',RF12BC,'probabilityMapsLeftThalamus')
    cutWF.connect(atlasObject,'probabilityMaps/r_thalamus_ProbabilityMap',RF12BC,'probabilityMapsRightThalamus')

    cutWF.connect(inputsSpec,'atlasToSubjectTransform',RF12BC,'deformationFromTemplateToSubject')
    RF12BC.inputs.modelFilename = '/tmp/model_here.mdl'

    outputsSpec = pe.Node(interface=IdentityInterface(fields=[
        'outputBinaryLeftAccumben','outputBinaryRightAccumben',
        'outputBinaryLeftCaudate','outputBinaryRightCaudate',
        'outputBinaryLeftGlobus','outputBinaryRightGlobus',
        'outputBinaryLeftHippocampus','outputBinaryRightHippocampus',
        'outputBinaryLeftPutamen','outputBinaryRightPutamen',
        'outputBinaryLeftThalamus','outputBinaryRightThalamus',
        'xmlFilename']), name='OutputSpec' )

    cutWF.connect(RF12BC,'outputBinaryLeftAccumben',outputsSpec,'outputBinaryLeftAccumben')
    cutWF.connect(RF12BC,'outputBinaryRightAccumben',outputsSpec,'outputBinaryRightAccumben')
    cutWF.connect(RF12BC,'outputBinaryLeftCaudate',outputsSpec,'outputBinaryLeftCaudate')
    cutWF.connect(RF12BC,'outputBinaryRightCaudate',outputsSpec,'outputBinaryRightCaudate')
    cutWF.connect(RF12BC,'outputBinaryLeftGlobus',outputsSpec,'outputBinaryLeftGlobus')
    cutWF.connect(RF12BC,'outputBinaryRightGlobus',outputsSpec,'outputBinaryRightGlobus')
    cutWF.connect(RF12BC,'outputBinaryLeftHippocampus',outputsSpec,'outputBinaryLeftHippocampus')
    cutWF.connect(RF12BC,'outputBinaryRightHippocampus',outputsSpec,'outputBinaryRightHippocampus')
    cutWF.connect(RF12BC,'outputBinaryLeftPutamen',outputsSpec,'outputBinaryLeftPutamen')
    cutWF.connect(RF12BC,'outputBinaryRightPutamen',outputsSpec,'outputBinaryRightPutamen')
    cutWF.connect(RF12BC,'outputBinaryLeftThalamus',outputsSpec,'outputBinaryLeftThalamus')
    cutWF.connect(RF12BC,'outputBinaryRightThalamus',outputsSpec,'outputBinaryRightThalamus')
    cutWF.connect(RF12BC,'xmlFilename',outputsSpec,'xmlFilename')

    return cutWF



    ############ Garbage Do not run!!!
def DontuseThis():



    """
    Load the BRAINSCut models & probabiity maps.
    """
    BCM_outputs = ['phi','rho','theta',
                   'r_probabilityMaps','l_probabilityMaps',
                   'models']
    BCM_Models = pe.Node(interface=nio.DataGrabber(input_names=['structures'],
                                                   outfields=BCM_outputs),
                         name='10_BCM_Models')
    BCM_Models.inputs.base_directory = atlas_fname_wpath
    BCM_Models.inputs.template_args['phi'] = [['spatialImages','phi','nii.gz']]
    BCM_Models.inputs.template_args['rho'] = [['spatialImages','rho','nii.gz']]
    BCM_Models.inputs.template_args['theta'] = [['spatialImages','theta','nii.gz']]
    BCM_Models.inputs.template_args['r_probabilityMaps'] = [['structures']]
    BCM_Models.inputs.template_args['l_probabilityMaps'] = [['structures']]
    BCM_Models.inputs.template_args['models'] = [['structures']]

    BRAINSCut_structures = ['caudate','thalamus','putamen','hippocampus']
    #BRAINSCut_structures = ['caudate','thalamus']
    BCM_Models.iterables = ( 'structures',  BRAINSCut_structures )
    BCM_Models.inputs.template = '%s/%s.%s'
    BCM_Models.inputs.field_template = dict(
        r_probabilityMaps='probabilityMaps/r_%s_ProbabilityMap.nii.gz',
        l_probabilityMaps='probabilityMaps/l_%s_ProbabilityMap.nii.gz',
        models='modelFiles/%sModel*',
        )

    """
    The xml creation and BRAINSCut need to be their own mini-pipeline that gets
    executed once for each of the structures in BRAINSCut_structures.  This can be
    accomplished with a map node and a new pipeline.
    """
    """
    Create xml file for BRAINSCut
    """


    BFitAtlasToSubject = pe.Node(interface=BRAINSFit(),name="BFitAtlasToSubject")
    BFitAtlasToSubject.inputs.costMetric="MMI"
    BFitAtlasToSubject.inputs.maskProcessingMode="ROI"
    BFitAtlasToSubject.inputs.numberOfSamples=100000
    BFitAtlasToSubject.inputs.numberOfIterations=[1500,1500]
    BFitAtlasToSubject.inputs.numberOfHistogramBins=50
    BFitAtlasToSubject.inputs.maximumStepLength=0.2
    BFitAtlasToSubject.inputs.minimumStepLength=[0.005,0.005]
    BFitAtlasToSubject.inputs.transformType= ["Affine","BSpline"]
    BFitAtlasToSubject.inputs.maxBSplineDisplacement= 7
    BFitAtlasToSubject.inputs.maskInferiorCutOffFromCenter=65
    BFitAtlasToSubject.inputs.splineGridSize=[28,20,24]
    BFitAtlasToSubject.inputs.outputVolume="Trial_Initializer_Output.nii.gz"
    BFitAtlasToSubject.inputs.outputTransform="Trial_Initializer_Output.mat"
    cutWF.connect(SplitAvgBABC,'avgBABCT1',BFitAtlasToSubject,'fixedVolume')
    cutWF.connect(BABC,'outputLabels',BFitAtlasToSubject,'fixedBinaryVolume')
    cutWF.connect(BAtlas,'template_t1',BFitAtlasToSubject,'movingVolume')
    cutWF.connect(BAtlas,'template_brain',BFitAtlasToSubject,'movingBinaryVolume')
    cutWF.connect(BLI,'outputTransformFilename',BFitAtlasToSubject,'initialTransform')

    CreateBRAINSCutXML = pe.Node(Function(input_names=['rho','phi','theta',
                                                          'model',
                                                          'r_probabilityMap',
                                                          'l_probabilityMap',
                                                          'atlasT1','atlasBrain',
                                                          'subjT1','subjT2',
                                                          'subjT1GAD','subjT2GAD',
                                                          'subjSGGAD','subjBrain',
                                                          'atlasToSubj','output_dir'],
                                             output_names=['xml_filename','rl_structure_filename_list'],
                                             function = create_BRAINSCut_XML),
                                    overwrite = True,
                                    name="CreateBRAINSCutXML")

    ## HACK  Makde better directory
    CreateBRAINSCutXML.inputs.output_dir = "." #os.path.join(cutWF.base_dir, "BRAINSCut_output")
    cutWF.connect(BCM_Models,'models',CreateBRAINSCutXML,'model')
    cutWF.connect(BCM_Models,'rho',CreateBRAINSCutXML,'rho')
    cutWF.connect(BCM_Models,'phi',CreateBRAINSCutXML,'phi')
    cutWF.connect(BCM_Models,'theta',CreateBRAINSCutXML,'theta')
    cutWF.connect(BCM_Models,'r_probabilityMaps',CreateBRAINSCutXML,'r_probabilityMap')
    cutWF.connect(BCM_Models,'l_probabilityMaps',CreateBRAINSCutXML,'l_probabilityMap')
    cutWF.connect(BAtlas,'template_t1',CreateBRAINSCutXML,'atlasT1')
    cutWF.connect(BAtlas,'template_brain',CreateBRAINSCutXML,'atlasBrain')
    cutWF.connect(SplitAvgBABC,'avgBABCT1',CreateBRAINSCutXML,'subjT1')
    cutWF.connect(SplitAvgBABC,'avgBABCT2',CreateBRAINSCutXML,'subjT2')
    cutWF.connect(GADT1,'outputVolume',CreateBRAINSCutXML,'subjT1GAD')
    cutWF.connect(GADT2,'outputVolume',CreateBRAINSCutXML,'subjT2GAD')
    cutWF.connect(SGI,'outputFileName',CreateBRAINSCutXML,'subjSGGAD')
    cutWF.connect(BABC,'outputLabels',CreateBRAINSCutXML,'subjBrain')
    cutWF.connect(BFitAtlasToSubject,'outputTransform',CreateBRAINSCutXML,'atlasToSubj')
    #CreateBRAINSCutXML.inputs.atlasToSubj = "INTERNAL_REGISTER.mat"
    #cutWF.connect(BABC,'atlasToSubjectTransform',CreateBRAINSCutXML,'atlasToSubj')

    """
     ResampleNACLabels
     """
     ResampleAtlasNACLabels=pe.Node(interface=BRAINSResample(),name="ResampleAtlasNACLabels")
     ResampleAtlasNACLabels.inputs.interpolationMode = "NearestNeighbor"
     ResampleAtlasNACLabels.inputs.outputVolume = "atlasToSubjectNACLabels.nii.gz"

     cutWF.connect(myLocalTCWF,'OutputSpec.atlasToSubjectTransform',ResampleAtlasNACLabels,'warpTransform')
     cutWF.connect(myLocalTCWF,'OutputSpec.t1_corrected',ResampleAtlasNACLabels,'referenceVolume')
     cutWF.connect(BAtlas,'template_nac_lables',ResampleAtlasNACLabels,'inputVolume')

     """
     BRAINSMush
     """
     BMUSH=pe.Node(interface=BRAINSMush(),name="BMUSH")
     BMUSH.inputs.outputVolume = "MushImage.nii.gz"
     BMUSH.inputs.outputMask = "MushMask.nii.gz"
     BMUSH.inputs.lowerThresholdFactor = 1.2
     BMUSH.inputs.upperThresholdFactor = 0.55

     cutWF.connect(myLocalTCWF,'OutputSpec.t1_corrected',BMUSH,'inputFirstVolume')
     cutWF.connect(myLocalTCWF,'OutputSpec.t2_corrected',BMUSH,'inputSecondVolume')
     cutWF.connect(myLocalTCWF,'OutputSpec.outputLabels',BMUSH,'inputMaskVolume')

     """
     BRAINSROIAuto
     """
     BROI = pe.Node(interface=BRAINSROIAuto(), name="BRAINSROIAuto")
     BROI.inputs.closingSize=12
     BROI.inputs.otsuPercentileThreshold=0.01
     BROI.inputs.thresholdCorrectionFactor=1.0
     BROI.inputs.outputROIMaskVolume = "temproiAuto_t1_ACPC_corrected_BRAINSABC.nii.gz"
     cutWF.connect(myLocalTCWF,'OutputSpec.t1_corrected',BROI,'inputVolume')

     """
     Split the implicit outputs of BABCext
     """
     SplitAvgBABC = pe.Node(Function(input_names=['in_files','T1_count'], output_names=['avgBABCT1','avgBABCT2'],
                              function = get_first_T1_and_T2), run_without_submitting=True, name="99_SplitAvgBABC")
     SplitAvgBABC.inputs.T1_count = 1 ## There is only 1 average T1 image.

     cutWF.connect(myLocalTCWF,'OutputSpec.outputAverageImages',SplitAvgBABC,'in_files')



     def printFullPath(outFileFullPath):
         print("="*80)
         print("="*80)
         print("="*80)
         print("="*80)
         print("{0}".format(outFileFullPath))
         return outFileFullPath
     printOutImage = pe.Node( Function(function=printFullPath, input_names = ['outFileFullPath'], output_names = ['genoutFileFullPath']), run_without_submitting=True, name="99_printOutImage")
     cutWF.connect( GADT2, 'outputVolume', printOutImage, 'outFileFullPath' )

def create_BRAINSCut_XML(rho,phi,theta,model,
                         r_probabilityMap,l_probabilityMap,
                         atlasT1,atlasBrain,
                         subjT1,subjT2,
                         subjT1GAD,subjT2GAD,subjSGGAD,subjBrain,
                         atlasToSubj,
                         output_dir):
    import re
    import os
    print "*"*80
    print rho
    print phi
    print theta
    print model
    print r_probabilityMap
    print l_probabilityMap
    structure = re.search("r_(\w+)_ProbabilityMap",os.path.basename(r_probabilityMap)).group(1)

    ## The model file name is auto-generated, and needs to be split apart here
    basemodel      =re.search("(.*{structure}Model.*\.txt)(00[0-9]*)".format(structure=structure),model).group(1)
    EpochIterations=re.search("(.*{structure}Model.*\.txt)(00[0-9]*)".format(structure=structure),model).group(2)
    EpochIterations.lstrip('0')

    ## HACK:  Needed to make neural networks easier to use.  This information should be embeded in the model file.
    HiddenNodeDict={'caudate':"14",'putamen':"20",'hippocampus':"20",'thalamus':"14"}

    print "^^"*80
    print "^^"*80
    print "^^"*80
    print "^^"*80
    print basemodel
    print EpochIterations
    NumberOfHiddenNodes=HiddenNodeDict[structure]

    EXTRA_FLAGS=""
    if structure in [ 'putamen','hippocampus']:
        EXTRA_FLAGS="""
     <Image Type="T1GAD" Filename="na" />
     <Image Type="T2GAD" Filename="na" />"""

    XMLSTRING="""<AutoSegProcessDescription>
  <RegistrationConfiguration
         ImageTypeToUse="T1-30"
         ID="BSpline_ROI"
         BRAINSROIAutoDilateSize="1"
  />
  <ANNParams
         Iterations="{EpochIterations}"
         MaximumVectorsPerEpoch="700000"
         EpochIterations="{EpochIterations}"
         ErrorInterval="1"
         DesiredError="0.000001"
         NumberOfHiddenNodes="{NumberOfHiddenNodes}"
         ActivationSlope="1.0"
         ActivationMinMax="1.0"
  />
  <ApplyModel
         CutOutThresh="0.05"
         MaskThresh="0.4"
         LevelSetImageType="NA"
         GaussianSmoothingSigma="0.0"
  />
  <NeuralNetParams
         MaskSmoothingValue="0.0"
         GradientProfileSize="1"
         TrainingVectorFilename="na"
         TrainingModelFilename="{basemodel}"
         TestVectorFilename="na"
         Normalization="true"
  />
  <ProbabilityMap StructureID="l_{structure}" Gaussian="0.5" GenerateVector="true" Filename="{l_probabilityMap}"/>
  <ProbabilityMap StructureID="r_{structure}" Gaussian="0.5" GenerateVector="true" Filename="{r_probabilityMap}"/>
  <DataSet Type="Atlas" Name="template">
    <Image Type="T1-30" Filename="{atlasT1}"/>
    <Image Type="T2-30" Filename="na"/>
    {EXTRA_FLAGS}
    <Image Type="SGGAD" Filename="na"/>

    <SpatialLocation Type="rho"   Filename="{rho}"/>
    <SpatialLocation Type="phi"   Filename="{phi}"/>
    <SpatialLocation Type="theta" Filename="{theta}"/>
  </DataSet>
  <DataSet Name="sessionID" Type="Apply" OutputDir="./">
      <Image Type="T1-30" Filename="{subjT1}"/>
      <Image Type="T2-30" Filename="{subjT2}"/>
      <Image Type="T1GAD" Filename="{subjT1GAD}"/>
      <Image Type="T2GAD" Filename="{subjT2GAD}"/>
      <Image Type="SGGAD" Filename="{subjSGGAD}"/>
      <Mask Type="l_{structure}" Filename="{output_dir}/l_{structure}_seg.nii.gz"/>
      <Mask Type="r_{structure}" Filename="{output_dir}/r_{structure}_seg.nii.gz"/>
      <Registration SubjToAtlasRegistrationFilename="na"
                    AtlasToSubjRegistrationFilename="{atlasToSubj}"
                    SubjectBinaryFilename="{subjBrain}"
                    AtlasBinaryFilename="{atlasBrain}"
                    ID="BSpline_ROI"/>
  </DataSet>
</AutoSegProcessDescription>
""".format(structure=structure,rho=rho,phi=phi,theta=theta,
                         basemodel=basemodel,EpochIterations=EpochIterations,NumberOfHiddenNodes=NumberOfHiddenNodes,
                         r_probabilityMap=r_probabilityMap,l_probabilityMap=l_probabilityMap,
                         atlasT1=atlasT1,atlasBrain=atlasBrain,
                         subjT1=subjT1,subjT2=subjT2,
                         subjT1GAD=subjT1GAD,subjT2GAD=subjT2GAD,subjSGGAD=subjSGGAD,subjBrain=subjBrain,
                         EXTRA_FLAGS=EXTRA_FLAGS,
                         atlasToSubj=atlasToSubj,
                         output_dir=output_dir)

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    #xml_filename = os.path.join(output_dir,'%s.xml' % structure)
    xml_filename = '%s.xml' % structure
    xml_file = open(xml_filename,'w')
    #xml_file.write(etree.tostring(xml_output, pretty_print=True))
    xml_file.write(XMLSTRING)
    xml_file.close()

    r_struct_fname="{output_dir}/r_{structure}_seg.nii.gz".format(output_dir=output_dir,structure=structure)
    l_struct_fname="{output_dir}/l_{structure}_seg.nii.gz".format(output_dir=output_dir,structure=structure)
    return os.path.realpath(xml_filename), [ r_struct_fname, l_struct_fname ]


