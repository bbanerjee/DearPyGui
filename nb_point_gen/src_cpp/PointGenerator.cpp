#include <PointGenerator.hpp>
#include <iostream>

namespace cpp_fns {

std::mt19937 PointGenerator::s_rng(std::random_device{}());
std::uniform_real_distribution<double> PointGenerator::s_dist(0.0, 1.0);

Eigen::Vector3d
PointGenerator::point_in_triangle(const Eigen::Vector3d& p1,
                                  const Eigen::Vector3d& p2,
                                  const Eigen::Vector3d& p3)
{
    double r1 = s_dist(s_rng);
    double r2 = s_dist(s_rng);

    if (r1 + r2 > 1.0) {
        r1 = 1.0 - r1;
        r2 = 1.0 - r2;
    }
    double r3 = 1.0 - r1 - r2;
    return Eigen::Vector3d(r1 * p1 + r2 * p2 + r3 * p3);
}

bool
PointGenerator::is_point_inside_mesh(const Eigen::Vector3d& point,
                                     const Eigen::MatrixXd& vertices,
                                     const Eigen::MatrixXi& faces)
{
    Eigen::Vector3d ray_dir(1.0, 0.0, 0.0);
    int intersections = 0;

    for (int ii = 0; ii < faces.rows(); ++ii) {
        Eigen::Vector3d v0 = vertices.row(faces(ii, 0));
        Eigen::Vector3d v1 = vertices.row(faces(ii, 1));
        Eigen::Vector3d v2 = vertices.row(faces(ii, 2));

        Eigen::Vector3d edge1 = v1 - v0;
        Eigen::Vector3d edge2 = v2 - v0;

        Eigen::Vector3d h = ray_dir.cross(edge2);
        double a = edge1.dot(h);

        if (std::abs(a) < 1.0e-8) {
            continue;
        }

        double f = 1.0 / a;
        Eigen::Vector3d s = point - v0;
        double u = f * s.dot(h);

        if (u < 0.0 || u > 1.0) {
            continue;
        }

        Eigen::Vector3d q = s.cross(edge1);
        double v = f * ray_dir.dot(q);

        if (v < 0.0 || u + v > 1.0) {
            continue;
        }

        double t = f * edge2.dot(q);

        if (t > 1.0e-8) { // Ray intersects triangle
            intersections++;
        }
    }

    return intersections % 2 == 1;
}

Eigen::MatrixXd
PointGenerator::generate_interior_points(
  const Eigen::MatrixXd& vertices,
  const Eigen::MatrixXi& faces,
  int num_points,
  std::function<void(int, int)> progress_callback)
{
    if (vertices.rows() == 0) {
        return Eigen::MatrixXd::Zero(0, 3); // Return an empty 0x3 matrix
    }

    // Get bounding box
    Eigen::Vector3d min_bounds = vertices.colwise().minCoeff();
    Eigen::Vector3d max_bounds = vertices.colwise().maxCoeff();

    std::vector<Eigen::Vector3d> interior_points;
    interior_points.reserve(num_points); // Pre-allocate memory

    std::mt19937 local_rng(std::random_device{}()); // Use a local RNG for generate_interior_points
    // Ensure uniform_real_distribution uses the min and max bounds for each dimension
    std::uniform_real_distribution<double> x_dist(min_bounds.x(), max_bounds.x());
    std::uniform_real_distribution<double> y_dist(min_bounds.y(), max_bounds.y());
    std::uniform_real_distribution<double> z_dist(min_bounds.z(), max_bounds.z());

    int attempts = 0;
    int max_attempts = num_points * 100; // Prevent infinite loops

    while (static_cast<int>(interior_points.size()) < num_points && attempts < max_attempts) {
        // Generate random point in bounding box
        Eigen::Vector3d point(x_dist(local_rng), y_dist(local_rng), z_dist(local_rng));

        if (PointGenerator::is_point_inside_mesh(point, vertices, faces)) {
            interior_points.push_back(point);

            // Report progress every 10 points
            if (progress_callback && interior_points.size() % 10 == 0) {
                progress_callback(static_cast<int>(interior_points.size()), num_points);
            }
        }
        attempts++;
    }

    // Convert std::vector<Eigen::Vector3d> to Eigen::MatrixXd
    Eigen::MatrixXd result(interior_points.size(), 3);
    for (size_t i = 0; i < interior_points.size(); ++i) {
        result.row(i) = interior_points[i];
    }

    return result;
}

} // namespace cpp_fns