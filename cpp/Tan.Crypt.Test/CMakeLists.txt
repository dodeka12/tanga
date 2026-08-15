# SPDX-License-Identifier: Apache-2.0
# Copyright 2021 Christian Perwass

cmake_minimum_required(VERSION 3.12)

include_directories(PUBLIC ${CMAKE_SOURCE_DIR}/cpp)
link_libraries(tan.core tan.math)

if(MSVC)
    add_compile_options(/arch:SSE4.1)
elseif(CMAKE_SYSTEM_PROCESSOR MATCHES "x86_64|AMD64|i[3-6]86")
    add_compile_options("-msse4.1")
    add_compile_options("-mpopcnt")
endif()

# Shared helper library — also consumed by Test_Basics_01 and Test_Basics_02
# in Tan.App.Test. PUBLIC include exposes this directory to consumers so that
# #include "Test_Crypt_Func.h" resolves without source changes.
add_library(tan.crypt.test.func STATIC Test_Crypt_Func.cpp)
target_include_directories(tan.crypt.test.func PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})

add_executable(Test_Crypt_02 Test_Crypt_02.cpp)
target_link_libraries(Test_Crypt_02 PRIVATE tan.crypt.test.func)
add_test(NAME Test_Crypt_02 COMMAND Test_Crypt_02)

add_executable(Test_Crypt_03 Test_Crypt_03.cpp)
target_link_libraries(Test_Crypt_03 PRIVATE tan.crypt.test.func)
add_test(NAME Test_Crypt_03 COMMAND Test_Crypt_03)

add_executable(Test_Crypt_04 Test_Crypt_04.cpp)
target_link_libraries(Test_Crypt_04 PRIVATE tan.crypt.test.func)
add_test(NAME Test_Crypt_04 COMMAND Test_Crypt_04)
