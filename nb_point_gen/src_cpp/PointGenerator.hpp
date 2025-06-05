#pragma once

#include <Eigen/Dense>
#include <functional>
#include <random>
#include <vector>

namespace cpp_fns {

class PointGenerator
{
  public:
    static Eigen::Vector3d
    point_in_triangle(const Eigen::Vector3d& p1,
                      const Eigen::Vector3d& p2,
                      const Eigen::Vector3d& p3);

    static bool
    is_point_inside_mesh(const Eigen::Vector3d& point,
                         const Eigen::MatrixXd& vertices,
                         const Eigen::MatrixXi& faces);

    static Eigen::MatrixXd
    generate_interior_points(
      const Eigen::MatrixXd& vertices,
      const Eigen::MatrixXi& faces,
      int num_points,
      std::function<void(int, int)> progress_callback = nullptr);

  private:
    static std::mt19937 s_rng;
    static std::uniform_real_distribution<double> s_dist;
};

} // namespace cpp_fns
