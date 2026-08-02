# //////////////////////////////////////////////////////////////////////////////////
# // <<licence: start>>
# //
# // This file is part of the TANGA library, 
# // a template library that implements geometric algebra.
# //
# // Copyright 2022 Christian Perwass
# //
# //    Licensed under the Apache License, Version 2.0 (the "License");
# //    you may not use this file except in compliance with the License.
# //    You may obtain a copy of the License at
# //
# //        http://www.apache.org/licenses/LICENSE-2.0
# //
# //    Unless required by applicable law or agreed to in writing, software
# //    distributed under the License is distributed on an "AS IS" BASIS,
# //    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# //    See the License for the specific language governing permissions and
# //    limitations under the License.
# //
# // <<licence: end>>
# //////////////////////////////////////////////////////////////////////////////////


cmake_minimum_required(VERSION 3.12)
project(tanga VERSION 0.1.0)

set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

set_property(GLOBAL PROPERTY CXX_STANDARD 17)

add_subdirectory(cpp/Tan.Core)
add_subdirectory(cpp/Tan.Math)
add_subdirectory(cpp/Tan.GA)
add_subdirectory(cpp/Tan.Crypt.Test)
add_subdirectory(cpp/Tan.App.Test)

set(CPACK_PROJECT_NAME ${PROJECT_NAME})
set(CPACK_PROJECT_VERSION ${PROJECT_VERSION})
# set(CMAKE_VERBOSE_MAKEFILE ON)

