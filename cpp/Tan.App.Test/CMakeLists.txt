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

include_directories(PUBLIC ${CMAKE_SOURCE_DIR}/cpp)
link_libraries(tan.core tan.math)

if(MSVC)
    add_compile_options(/arch:SSE4.1)
else()
    add_compile_options("-msse4.1")
    add_compile_options("-mpopcnt")
endif()

add_executable(Test_Math_01 Test_Math_01.cpp)
add_test(NAME Test_Math_01 COMMAND Test_Math_01)

add_executable(Test_Array Test_Array.cpp)
add_test(NAME Test_Array COMMAND Test_Array)

add_executable(Test_Basics_01 Test_Basics_01.cpp)
target_link_libraries(Test_Basics_01 PRIVATE tan.crypt.test.func)
add_test(NAME Test_Basics_01 COMMAND Test_Basics_01)

add_executable(Test_Basics_02 Test_Basics_02.cpp)
target_link_libraries(Test_Basics_02 PRIVATE tan.crypt.test.func)
add_test(NAME Test_Basics_02 COMMAND Test_Basics_02)

add_executable(Test_Matrix_01 Test_Matrix_01.cpp)
add_test(NAME Test_Matrix_01 COMMAND Test_Matrix_01)

add_executable(Test_Matrix_GE_01 Test_Matrix_GE_01.cpp)
add_test(NAME Test_Matrix_GE_01 COMMAND Test_Matrix_GE_01)

add_executable(Test_Matrix_GE_02 Test_Matrix_GE_02.cpp)
add_test(NAME Test_Matrix_GE_02 COMMAND Test_Matrix_GE_02)

add_executable(Test_ModMVRing Test_ModMVRing.cpp)
add_test(NAME Test_ModMVRing COMMAND Test_ModMVRing)

add_executable(Test_MV_Blade_Ops Test_MV_Blade_Ops.cpp)
add_test(NAME Test_MV_Blade_Ops COMMAND Test_MV_Blade_Ops)



