cmake_minimum_required(VERSION 3.10)
project(udf_app)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(plugin_api SHARED
    plugin_api_impl.cpp
)
