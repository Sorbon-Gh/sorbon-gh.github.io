from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files('pyqtgraph', include_py_files=False)

hiddenimports = [
    'pyqtgraph.graphicsItems',
    'pyqtgraph.graphicsItems.PlotItem',
    'pyqtgraph.graphicsItems.ViewBox',
    'pyqtgraph.graphicsItems.AxisItem',
    'pyqtgraph.graphicsItems.PlotDataItem',
    'pyqtgraph.graphicsItems.ImageItem',
    'pyqtgraph.graphicsItems.ScatterPlotItem',
    'pyqtgraph.graphicsItems.GraphicsObject',
    'pyqtgraph.widgets',
    'pyqtgraph.widgets.PlotWidget',
    'pyqtgraph.widgets.GraphicsLayoutWidget',
    'pyqtgraph.colormap',
]

excludedimports = [
    'pyqtgraph.opengl',
    'pyqtgraph.canvas',
    'pyqtgraph.examples',
    'OpenGL',
]
