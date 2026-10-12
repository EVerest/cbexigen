/* SPDX-License-Identifier: Apache-2.0 */
/*
 * Copyright (C) 2022 - 2026 chargebyte GmbH
 * Copyright (C) 2022 - 2026 Contributors to EVerest
 */

/*
 * Decodes one ISO 15118-2 EXI document, encodes it again and prints the result.
 *
 * Prints decode=<rc>, then, when decoding succeeded, encode=<rc> and, when
 * encoding succeeded too, the re-encoded bytes as uppercase hex on their own
 * line. Exits 0 only when both succeed.
 *
 * usage: iso2_roundtrip_driver <EXI hex>
 */
#include <stdio.h>
#include <string.h>

#include "exi_bitstream.h"
#include "iso2_msgDefDecoder.h"
#include "iso2_msgDefEncoder.h"

#define BUFFER_SIZE 4096

static int hex_value(char c) {
    if (c >= '0' && c <= '9') {
        return c - '0';
    }
    if (c >= 'a' && c <= 'f') {
        return c - 'a' + 10;
    }
    if (c >= 'A' && c <= 'F') {
        return c - 'A' + 10;
    }
    return -1;
}

int main(int argc, char** argv) {
    static uint8_t input[BUFFER_SIZE];
    static uint8_t output[BUFFER_SIZE];
    static struct iso2_exiDocument document;
    exi_bitstream_t stream;
    size_t hex_length;
    size_t length;
    int error;

    if (argc != 2) {
        fprintf(stderr, "usage: %s <EXI hex>\n", argv[0]);
        return 2;
    }

    hex_length = strlen(argv[1]);
    if (hex_length % 2 != 0 || hex_length / 2 > sizeof(input)) {
        fprintf(stderr, "hex input of %zu chars is odd or too long\n", hex_length);
        return 2;
    }
    for (size_t i = 0; i < hex_length / 2; i++) {
        int high = hex_value(argv[1][2 * i]);
        int low = hex_value(argv[1][2 * i + 1]);
        if (high < 0 || low < 0) {
            fprintf(stderr, "not a hex digit at offset %zu\n", 2 * i);
            return 2;
        }
        input[i] = (uint8_t)(high << 4 | low);
    }

    exi_bitstream_init(&stream, input, hex_length / 2, 0, NULL);
    error = decode_iso2_exiDocument(&stream, &document);
    printf("decode=%d\n", error);
    if (error != 0) {
        return 1;
    }

    exi_bitstream_init(&stream, output, sizeof(output), 0, NULL);
    error = encode_iso2_exiDocument(&stream, &document);
    printf("encode=%d\n", error);
    if (error != 0) {
        return 1;
    }

    length = exi_bitstream_get_length(&stream);
    for (size_t i = 0; i < length; i++) {
        printf("%02X", output[i]);
    }
    printf("\n");

    return 0;
}
