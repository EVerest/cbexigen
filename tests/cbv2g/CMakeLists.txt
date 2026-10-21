cmake_minimum_required(VERSION 3.18)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

set(CBV2G_SOURCE_PATH "../../src/output/c")

file(GLOB_RECURSE CBV2G_SOURCES
    ${CBV2G_SOURCE_PATH}/common/*.c
    ${CBV2G_SOURCE_PATH}/appHandshake/*.c
    ${CBV2G_SOURCE_PATH}/din/*.c
    ${CBV2G_SOURCE_PATH}/iso-2/*.c
    ${CBV2G_SOURCE_PATH}/iso-20/*.c
    ${CBV2G_SOURCE_PATH}/v2gtp/*.c
)

add_library(cbv2g STATIC
    ${CBV2G_SOURCES}
)

target_compile_options(cbv2g PRIVATE -Werror -Wall -Wextra)

target_include_directories(cbv2g
    PUBLIC
        ${CBV2G_SOURCE_PATH}/
        ${CBV2G_SOURCE_PATH}/appHandshake
        ${CBV2G_SOURCE_PATH}/common
        ${CBV2G_SOURCE_PATH}/din
        ${CBV2G_SOURCE_PATH}/iso-2
        ${CBV2G_SOURCE_PATH}/iso-20
        ${CBV2G_SOURCE_PATH}/v2gtp
)
