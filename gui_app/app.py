# app.py
from dearpygui.dearpygui import *
from viewer_3d import Viewer3D

class PipelineApp:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.node_editor = "node_editor"
            cls._instance.nodes = {}              # tag → node instance
            cls._instance.viewer_3d = Viewer3D()
        return cls._instance

    @property
    def viewer(self):
        return self._instance.viewer_3d

# Convenience accessor
def get_app_singleton():
    return PipelineApp()