# app.py
from dearpygui.dearpygui import *
from viewer_3d import Viewer3D

import math

class PipelineApp:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.node_editor = "node_editor"
            cls._instance.nodes = {}              # tag → node instance
            cls._instance.viewer_3d = Viewer3D()

            # ←←← Auto-layout state
            cls._instance._layout_angle = 0.0
            cls._instance._layout_radius = 200.0
            cls._instance._layout_spiral_step = 80.0

        return cls._instance

    @property
    def viewer(self):
        return self._instance.viewer_3d

    def get_next_node_position(self):
        """Golden-angle spiral layout — always finds free space"""
        app = self._instance

        # Golden angle in radians
        angle = app._layout_angle
        radius = app._layout_radius

        x = 300 + radius * math.cos(angle)
        y = 200 + radius * math.sin(angle)

        # Update for next node
        app._layout_angle += 2.39996  # ~137.5° golden angle in radians
        app._layout_radius += app._layout_spiral_step / (2 * math.pi)

        # Optional: reset spiral after ~30 nodes
        if app._layout_radius > 1200:
            app._layout_radius = 200
            app._layout_angle = 0

        return [x, y]

    def reset_layout(self):
        self._instance._layout_angle = 0.0
        self._instance._layout_radius = 200.0


# Convenience accessor
def get_app_singleton():
    return PipelineApp()