#include <nanobind/nanobind.h>
#include <test_fn.hpp>

namespace nb = nanobind;

NB_MODULE(test_cpp_lib, m) {
    m.doc() = "nanobind plugin";

    m.def("add_integers", &cpp_fns::add_int, "Adds two ints");
    m.def("multiply_double", &cpp_fns::mult_double, "Multiply two doubles");
}