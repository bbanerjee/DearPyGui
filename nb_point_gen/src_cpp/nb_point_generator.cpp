#include <nanobind/eigen/dense.h>
#include <nanobind/nanobind.h>

#include <PointGenerator.hpp>

namespace nb = nanobind;

NB_MODULE(point_generator_cpp, m)
{
    m.doc() = "nanobind plugin";

    nb::class_<cpp_fns::PointGenerator>(m, "PointGenerator")
      .def_static(
        "point_in_triangle",
        &cpp_fns::PointGenerator::point_in_triangle,
        nb::arg("p1").noconvert(),
        nb::arg("p2").noconvert(),
        nb::arg("p3").noconvert(),
        "Generate random point inside triangle using barycentric coordinates")
      .def_static("is_point_inside_mesh",
                  &cpp_fns::PointGenerator::is_point_inside_mesh,
                  nb::arg("point").noconvert(),
                  nb::arg("vertices").noconvert(),
                  nb::arg("faces").noconvert(),
                  "Ray casting algorithm to check if point is inside mesh")
      .def_static(
        "generate_interior_points",
        [](const Eigen::MatrixXd& vertices,
           const Eigen::MatrixXi& faces,
           int num_points,
           nb::object progress_callback) {
            // Wrap the Python callable as a std::function
            std::function<void(int, int)> cpp_callback = nullptr;
            if (!progress_callback.is_none()) {
                cpp_callback = [progress_callback](int current, int total) {
                    // Acquire GIL before calling Python callable
                    nb::gil_scoped_acquire guard;
                    progress_callback(current, total);
                };
            }
            return cpp_fns::PointGenerator::generate_interior_points(
              vertices, faces, num_points, cpp_callback);
        },
        nb::arg("vertices").noconvert(),
        nb::arg("faces").noconvert(),
        nb::arg("num_points"),
        nb::arg("progress_callback") = nb::none(),
        "Generate points inside the mesh using rejection sampling");
}