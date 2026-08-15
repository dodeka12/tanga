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

file(GLOB HEADER_LIST CONFIGURE_DEPENDS "*.h")

add_library(TemplateGaCompileTest 
    _CompileTest_Objects.cpp 
    _CompileTest_Funcs.cpp 
    _CompileTest_Ops.cpp 
    ${HEADER_LIST})

target_include_directories(TemplateGaCompileTest PUBLIC ${CMAKE_SOURCE_DIR}/cpp)

if(MSVC)
    target_compile_options(TemplateGaCompileTest PUBLIC /arch:SSE4.1)
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64|i[3-6]86")
    target_compile_options(TemplateGaCompileTest PUBLIC "-msse4.1")
    target_compile_options(TemplateGaCompileTest PUBLIC "-mpopcnt")
endif()
