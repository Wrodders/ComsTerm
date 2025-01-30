import vtk

# Create a reader to load the STL file
reader = vtk.vtkSTLReader()
reader.SetFileName("Bodyv18.stl")

# Create a mapper and actor for the STL model
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(reader.GetOutputPort())
actor = vtk.vtkActor()
actor.SetMapper(mapper)

# Create a renderer, render window, and interactor
renderer = vtk.vtkRenderer()
render_window = vtk.vtkRenderWindow()
render_window.AddRenderer(renderer)
render_window_interactor = vtk.vtkRenderWindowInteractor()
render_window_interactor.SetRenderWindow(render_window)

# Add the actor to the renderer and start the interaction
renderer.AddActor(actor)
renderer.SetBackground(0.1, 0.1, 0.1)  # Set background color
render_window.Render()
render_window_interactor.Start()
