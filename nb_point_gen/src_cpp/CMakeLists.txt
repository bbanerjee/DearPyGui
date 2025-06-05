cmake_minimum_required(VERSION 3.15)
project(TestLib)

find_package(Python 3 COMPONENTS Interpreter Development.Module REQUIRED)

find_package(nanobind CONFIG REQUIRED)

find_package(Eigen3 CONFIG REQUIRED)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_library(point_generator_core SHARED
    PointGenerator.cpp
)

target_include_directories(point_generator_core PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${EIGEN3_INCLUDE_DIR}
)

nanobind_add_module(point_generator_cpp
    nb_point_generator.cpp
)

target_link_libraries(point_generator_cpp PRIVATE
    point_generator_core
    Eigen3::Eigen
)

set_target_properties(point_generator_cpp PROPERTIES 
    LIBRARY_OUTPUT_DIRECTORY "${PROJECT_BINARY_DIR}/python_lib"
)