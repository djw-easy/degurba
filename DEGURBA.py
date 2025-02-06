# -*- coding: utf-8 -*-

from qgis.core import (
    QgsProcessingProvider,
    QgsApplication,
    QgsProcessing,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterFileDestination,
    QgsProcessingException,
    QgsMessageLog,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterVectorDestination,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterString
)
from PyQt5.QtCore import QCoreApplication
from qgis.PyQt.QtGui import QIcon

from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm, QgsProcessingAlgorithm

from .degurba.load_data import wp_info, wp_datasets, Dataset, gpw_datasets
from .degurba.main import DEGURBA

import os

pluginPath = os.path.split(os.path.dirname(__file__))[0]


class DEGURBA_Plugin:
    def __init__(self, iface):
        self.provider = DEGURBA_Provider()

    def initGui(self):
        QgsApplication.processingRegistry().addProvider(self.provider)

    def unload(self):
        QgsApplication.processingRegistry().removeProvider(self.provider)


class DEGURBA_Provider(QgsProcessingProvider):
    def __init__(self):
        super().__init__()

    def id(self, *args, **kwargs):
        return 'DEGURBA_Provider'

    def name(self, *args, **kwargs):
        return 'DEGURBA'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'degurba', 'icon.svg'))

    def svgIconPath(self):
        return os.path.join(pluginPath, 'degurba', 'icon.svg')

    def loadAlgorithms(self, *args, **kwargs):
        self.addAlgorithm(DownloadWorldPopData())
        self.addAlgorithm(DownloadGPWV4Data())
        self.addAlgorithm(GridCellClassification())
        self.addAlgorithm(LocalUnitsClassification())


class DownloadWorldPopData(QgsProcessingAlgorithm):
    MASK = 'MASK LAYER'
    OUTPUT = 'OUTPUT'
    COUNTRY = 'COUNTRY'
    YEAR = 'YEAR'
    INPUT = 'DATASET'

    countries = list(wp_info.keys())
    years = wp_datasets['valid_years']
    years = [str(year) for year in years]
    datasets = list(wp_datasets.keys())[:-1]

    def name(self):
        return 'download worldpop grid data'

    def displayName(self, *args, **kwargs):
        return 'download worldpop grid data'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'degurba', 'icon.svg'))

    def shortHelpString(self):
        return 'Given an input polygon layer and a percentage value, this ' \
               'algorithm creates a buffer area for each feature so that the ' \
               'area of the buffered feature is the specified percentage of ' \
               'the area of the input feature.\n' \
               'For example, when specifying a percentage value of 200 %, ' \
               'the buffered features would have twice the area of the input ' \
               'features. For a percentage value of 50 %, the buffered ' \
               'features would have half the area of the input features.\n' \
               'The segments parameter controls the number of line segments ' \
               'to use to approximate a quarter circle when creating rounded ' \
               'offsets.'

    def outputName(self):
        return self.tr('Output data')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.MASK,
                self.tr('MASK layer'),
                [],
                None,
                True
            )
        )
        self.addParameter(QgsProcessingParameterEnum(self.INPUT,
                                                     self.tr('DATASET'), self.datasets, False, 0))
        self.addParameter(QgsProcessingParameterEnum(self.COUNTRY,
                                                     self.tr('COUNTRY'), self.countries, False, 0))
        self.addParameter(QgsProcessingParameterEnum(self.YEAR,
                                                     self.tr('YEAR'), self.years, False, 0))
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('OUTPUT RASTER')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        dataset = self.parameterAsEnum(parameters, self.INPUT, context)
        dataset = self.datasets[dataset]
        country = self.parameterAsEnum(parameters, self.COUNTRY, context)
        country = self.countries[country]
        year = self.parameterAsEnum(parameters, self.YEAR, context)
        year = self.years[year]

        mask_vector = self.parameterAsVectorLayer(parameters, self.MASK, context)
        mask_path = None
        if mask_vector is not None:
            mask_path = mask_vector.dataProvider().dataSourceUri()
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        log = '\n   %s \n   %s \n   %s \n   %s \n   %s \n' % (dataset, country, year, mask_path, output)
        print(log)
        QgsMessageLog.logMessage(log)

        dataset_dl = Dataset()
        if mask_path is None:
            dataset_dl.download(dataset, year, country, output)
        else:
            dataset_dl.download(dataset, year, country, output)
            dataset_dl.mask(mask_path)

        return {self.OUTPUT: output}

    def createInstance(self):
        return DownloadWorldPopData()

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)


class DownloadGPWV4Data(QgsProcessingAlgorithm):
    MASK = 'MASK LAYER'
    OUTPUT = 'OUTPUT'
    YEAR = 'YEAR'
    INPUT = 'DATASET'

    datasets = list(gpw_datasets.keys())[:-1]
    years = gpw_datasets['valid_years']
    years = [str(year) for year in years]

    def __init__(self):
        super().__init__()

    def name(self):
        return 'download gpwv4 grid data'

    def displayName(self, *args, **kwargs):
        return 'download gpwv4 grid data'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'degurba', 'icon.svg'))

    def shortHelpString(self):
        return 'Given an input polygon layer and a percentage value, this ' \
               'algorithm creates a buffer area for each feature so that the ' \
               'area of the buffered feature is the specified percentage of ' \
               'the area of the input feature.\n' \
               'For example, when specifying a percentage value of 200 %, ' \
               'the buffered features would have twice the area of the input ' \
               'features. For a percentage value of 50 %, the buffered ' \
               'features would have half the area of the input features.\n' \
               'The segments parameter controls the number of line segments ' \
               'to use to approximate a quarter circle when creating rounded ' \
               'offsets.'

    def outputName(self):
        return self.tr('Output data')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.MASK,
                self.tr('MASK layer'),
                [],
                None,
                True
            )
        )
        self.addParameter(QgsProcessingParameterEnum(self.INPUT,
                                                     self.tr('DATASET'), self.datasets, False, 0))
        self.addParameter(QgsProcessingParameterEnum(self.YEAR,
                                                     self.tr('YEAR'), self.years, False, 0))
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('OUTPUT RASTER')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        dataset = self.parameterAsEnum(parameters, self.INPUT, context)
        dataset = self.datasets[dataset]
        year = self.parameterAsEnum(parameters, self.INPUT, context)
        year = self.years[year]

        mask_vector = self.parameterAsVectorLayer(parameters, self.MASK, context)
        mask_path = None
        if mask_vector is not None:
            mask_path = mask_vector.dataProvider().dataSourceUri()
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        log = '\n   %s \n   %s \n   %s \n   %s \n' % (dataset, year, mask_path, output)
        print(log)
        QgsMessageLog.logMessage(log)

        dataset_dl = Dataset()
        if mask_path is None:
            dataset_dl.download(dataset, year, country=None, file_path=output)
        else:
            dataset_dl.download(dataset, year, country=None, file_path=output)
            dataset_dl.mask(mask_path)

        return {self.OUTPUT: output}

    def createInstance(self):
        return DownloadGPWV4Data()

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)


class GridCellClassification(QgsProcessingAlgorithm):
    INPUT = 'GRID POPULATION'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()

    def name(self):
        return 'GridCellClassification'

    def displayName(self, *args, **kwargs):
        return 'Grid Cell Classification'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'degurba', 'icon.svg'))

    def shortHelpString(self):
        return 'Given an input polygon layer and a percentage value, this ' \
               'algorithm creates a buffer area for each feature so that the ' \
               'area of the buffered feature is the specified percentage of ' \
               'the area of the input feature.\n' \
               'For example, when specifying a percentage value of 200 %, ' \
               'the buffered features would have twice the area of the input ' \
               'features. For a percentage value of 50 %, the buffered ' \
               'features would have half the area of the input features.\n' \
               'The segments parameter controls the number of line segments ' \
               'to use to approximate a quarter circle when creating rounded ' \
               'offsets.'

    def outputName(self):
        return self.tr('Output data')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('GRID POPULATION')
            )
        )
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr('OUTPUT RASTER')
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        raster_path = raster_layer.dataProvider().dataSourceUri()
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)

        log = '\n   %s \n   %s \n' % (raster_path, output)
        print(log)
        QgsMessageLog.logMessage(log)

        degurba = DEGURBA(raster_path)
        grid_cells_l1 = degurba.classify_grid_cells_l1()
        grid_cells_l1.save(output, nodata=0)

        return {self.OUTPUT: output}

    def createInstance(self):
        return GridCellClassification()

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)


class LocalUnitsClassification(QgsProcessingAlgorithm):
    INPUT = 'GRIDCELL'
    FIELD = 'FIELD'
    OUTPUT = 'LOCAL UNITS VECTOR'

    def __init__(self):
        super().__init__()

    def name(self):
        return 'LocalUnitsClassification'

    def displayName(self, *args, **kwargs):
        return 'Local Units Classification'

    def icon(self):
        return QIcon(os.path.join(pluginPath, 'degurba', 'icon.svg'))

    def shortHelpString(self):
        return 'Given an input polygon layer and a percentage value, this ' \
               'algorithm creates a buffer area for each feature so that the ' \
               'area of the buffered feature is the specified percentage of ' \
               'the area of the input feature.\n' \
               'For example, when specifying a percentage value of 200 %, ' \
               'the buffered features would have twice the area of the input ' \
               'features. For a percentage value of 50 %, the buffered ' \
               'features would have half the area of the input features.\n' \
               'The segments parameter controls the number of line segments ' \
               'to use to approximate a quarter circle when creating rounded ' \
               'offsets.'

    def outputName(self):
        return self.tr('Output data')

    def initAlgorithm(self, config=None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr('Grid Cell')
            )
        )
        self.addParameter(QgsProcessingParameterString(self.FIELD,
                                                       self.tr('FIELD'),
                                                       defaultValue='l1'))
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.OUTPUT,
                self.tr('Output Layer'),
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        raster_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        raster_path = raster_layer.dataProvider().dataSourceUri()

        field = self.parameterAsString(parameters, self.FIELD, context)

        vector_layer = self.parameterAsVectorLayer(parameters, self.OUTPUT, context)
        vector_path = vector_layer.dataProvider().dataSourceUri()

        log = '\n   %s \n   %s \n   %s \n' % (vector_path, raster_path, field)
        print(log)
        QgsMessageLog.logMessage(log)

        degurba = DEGURBA()
        local_units = degurba.classify_local_units_l1(vector_path,
                                                      grid_cells_l1=raster_path,
                                                      field=field,
                                                      all_touched=False)

        vector_layer.reload()

        return {self.OUTPUT: vector_path}

    def createInstance(self):
        return LocalUnitsClassification()

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)



