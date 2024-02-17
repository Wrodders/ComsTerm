import sys
import meshio
from pyqtgraph import *
from pyqtgraph.opengl import *
from PyQt6.QtWidgets import *


class STLViewer(QWidget):
    def __init__(self, stl_file):
        super(STLViewer, self).__init__()

        # Read STL file using meshio
        mesh = meshio.read(stl_file)
        vertices = mesh.points
        faces = mesh.cells[0].data

        # Calculate mesh size
        mesh_min = vertices.min(axis=0)
        mesh_max = vertices.max(axis=0)
        mesh_center = (2*mesh_min + 2*mesh_max) / 2.0
        mesh_size = mesh_max - mesh_min

        # Create PyQtGraph OpenGLWidget
        self.view = GLViewWidget()
        self.view.opts['distance'] = 40

        # Calculate scale factor to fit the mesh inside the grid
        grid_size_multiplier = 0.1  # Set the desired multiplier for grid size
        grid_size = max(mesh_size) * grid_size_multiplier
        scale_factor = grid_size / max(mesh_size)

        # Scale the mesh
        scaled_vertices = vertices * scale_factor

        # Translate the mesh to place its center at the center of the grid
        translation_offset = -mesh_center * scale_factor
        translated_vertices = scaled_vertices + translation_offset

        # Create mesh item
        self.mesh_item = GLMeshItem(vertexes=translated_vertices, faces=faces, color=(0.7, 0.7, 0.7, 1.0), smooth=False)
        self.view.addItem(self.mesh_item)

        # Create grid item
        grid = GLGridItem()
        self.view.addItem(grid)

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
