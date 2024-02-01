import sys
import meshio
from  pyqtgraph import * 
from pyqtgraph.opengl import *
from PyQt6 import QtCore
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *


class STLViewer(QWidget):
    def __init__(self, stl_file):
        super(STLViewer, self).__init__()

        # Read STL file using meshio
        mesh = meshio.read(stl_file)
        vertices = mesh.points
        faces = mesh.cells[0].data

        # Create PyQtGraph OpenGLWidget
        self.view = GLViewWidget()
        self.view.opts['distance'] = 40

        # Create mesh item
        self.mesh_item = GLMeshItem(vertexes=vertices, faces=faces, color=(0.7, 0.7, 0.7, 1.0), smooth=False)
        self.view.addItem(self.mesh_item)

        # Create layout
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        # Set up PyQtGraph window
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle('STL Viewer')
        self.show()

def main():
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_stl_file>")
        sys.exit(1)

    stl_file = sys.argv[1]

    app = QApplication(sys.argv)
    viewer = STLViewer(stl_file)
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
