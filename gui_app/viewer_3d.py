# viewer_3d.py
import dearpygui.dearpygui as dpg
import pymeshlab
import numpy as np

class Viewer3D:
    def __init__(self):
        self.window_tag = "3D Viewer"
        self.plot_tag = "plot3d"
        self.mesh_actor = None

    def show(self):
        if not dpg.does_item_exist(self.window_tag):
            with dpg.window(label="3D Viewer", width=800, height=600, tag=self.window_tag, pos=[100, 100]):
                with dpg.plot(no_title_bar=True, width=-1, height=-1):
                    dpg.add_plot_3d(tag=self.plot_tag, width=-1, height=-1,
                                    query=True, pan=True)

    def load_mesh(self, ml_mesh, wireframe=False, opacity=1.0):
        self.show()
        verts = np.array(ml_mesh.vertex_matrix(), dtype=float)
        faces = np.array(ml_mesh.face_matrix(), dtype=int) if ml_mesh.face_number() > 0 \
                else np.array(ml_mesh.cell_matrix()[:, :4], dtype=int)  # tet faces

        if self.mesh_actor:
            dpg.delete_item(self.mesh_actor)

        flat_faces = faces.flatten()
        color = [100, 180, 255, int(255 * opacity)]

        self.mesh_actor = dpg.add_mesh(
            parent=self.plot_tag,
            vertices=verts.tolist(),
            faces=flat_faces.tolist(),
            face_count=len(faces),
            color=color,
            shading=True,
            wireframe=wireframe
        )

        # Auto-fit view
        for axis in (dpg.mvXAxis, dpg.mvYAxis, dpg.mvZAxis):
            dpg.fit_axis_data(dpg.get_axis_tag(self.plot_tag, axis))

    def update(self):
        pass

# Global instance
viewer_3d = Viewer3D()