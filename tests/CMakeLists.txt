cmake_minimum_required(VERSION 3.14)

project(cbexigen VERSION 1)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

find_package(GTest)

add_subdirectory(cbv2g)

file(GLOB_RECURSE CBV2G_TEST_SOURCES
    ./unit/sap/*.cpp
    ./unit/iso20/common/*.cpp
    ./unit/iso2/*.cpp
    ./unit/xmldsig/*.cpp
)

add_executable(test-${PROJECT_NAME}
    ${CBV2G_TEST_SOURCES}
)

target_compile_options(test-${PROJECT_NAME} PRIVATE -Wall -Werror -Wshadow)

target_include_directories(test-${PROJECT_NAME}
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(test-${PROJECT_NAME}
PRIVATE
    gtest
    gtest_main
    gmock
    pthread
    cbv2g
)

include(GoogleTest)
gtest_discover_tests(test-${PROJECT_NAME}
    TEST_PREFIX ${PROJECT_NAME}
    TEST_LIST   ${PROJECT_NAME}Tests
)

set_tests_properties(${${PROJECT_NAME}Tests} PROPERTIES TIMEOUT 10)
