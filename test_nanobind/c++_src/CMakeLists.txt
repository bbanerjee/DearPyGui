cmake_minimum_required(VERSION 3.15)
project(TestLib)

find_package(Python 3 COMPONENTS Interpreter Development REQUIRED)

find_package(nanobind CONFIG REQUIRED)

add_library(test_fn SHARED
    test_fn.cpp
)

target_include_directories(test_fn PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}
)

nanobind_add_module(test_cpp_lib
    nanobind_sig.cpp
)

target_link_libraries(test_cpp_lib PRIVATE
    test_fn
)

set_target_properties(test_cpp_lib PROPERTIES 
    LIBRARY_OUTPUT_DIRECTORY "${PROJECT_BINARY_DIR}/python_lib"
)