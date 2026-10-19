// SPDX-License-Identifier: Apache-2.0
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "exi_basetypes.h"
#include "exi_basetypes_decoder.h"
#include "exi_basetypes_encoder.h"
#include "exi_bitstream.h"

enum operation {
    TO_SIGNED64, TO_SIGNED32, INTEGER64, INTEGER32,
    FROM_SIGNED64, FROM_SIGNED32, DECODE_INTEGER64, DECODE_INTEGER32, PARTS
};

static const struct {
    const char* name;
    enum operation operation;
    int argc;
} operations[] = {
    {"to_signed64", TO_SIGNED64, 3},
    {"to_signed32", TO_SIGNED32, 4},
    {"integer64", INTEGER64, 3},
    {"integer32", INTEGER32, 3},
    {"from_signed64", FROM_SIGNED64, 3},
    {"from_signed32", FROM_SIGNED32, 4},
    {"decode_integer64", DECODE_INTEGER64, 3},
    {"decode_integer32", DECODE_INTEGER32, 3},
    {"parts", PARTS, 3},
};

static void print_wire(int rc, const exi_bitstream_t* stream)
{
    printf("rc=%d wire=", rc);
    for (size_t i = 0; i < exi_bitstream_get_length(stream); i++) {
        printf("%02x", stream->data[i]);
    }
    putchar('\n');
}

int main(int argc, char** argv)
{
    size_t selected;
    for (selected = 0; selected < sizeof(operations) / sizeof(operations[0]); selected++) {
        if (argc > 1 && strcmp(argv[1], operations[selected].name) == 0) {
            break;
        }
    }
    if (selected == sizeof(operations) / sizeof(operations[0]) ||
        argc != operations[selected].argc) {
        return 2;
    }

    enum operation op = operations[selected].operation;
    uint8_t bytes[128] = {0};
    size_t length = sizeof(bytes);
    size_t max_octets = argc == 4 ? (size_t)strtoul(argv[3], NULL, 10) : 5;
    int64_t value64 = 123456789;
    int32_t value32 = 123456789;
    exi_signed_t signed_value = {0};
    exi_bitstream_t stream;
    int rc = 0;

    if (op >= FROM_SIGNED64) {
        size_t hex_length = strlen(argv[2]);
        if (hex_length % 2 != 0 || hex_length / 2 > sizeof(bytes)) {
            return 2;
        }
        length = hex_length / 2;
        for (size_t i = 0; i < length; i++) {
            char pair[3] = {argv[2][2 * i], argv[2][2 * i + 1], 0};
            char* end;
            unsigned long byte = strtoul(pair, &end, 16);
            if (end != pair + 2 || byte > 255) {
                return 2;
            }
            bytes[i] = (uint8_t)byte;
        }
    } else {
        value64 = strtoimax(argv[2], NULL, 10);
        value32 = (int32_t)value64;
    }
    exi_bitstream_init(&stream, bytes, length, 0, NULL);

    switch (op) {
    case TO_SIGNED64:
        rc = exi_basetypes_convert_64_to_signed(&signed_value, value64);
        if (rc == 0) {
            rc = exi_basetypes_encoder_signed(&stream, &signed_value);
        }
        print_wire(rc, &stream);
        break;
    case TO_SIGNED32:
        rc = exi_basetypes_convert_to_signed(&signed_value, value32, max_octets);
        if (rc == 0) {
            rc = exi_basetypes_encoder_signed(&stream, &signed_value);
        }
        print_wire(rc, &stream);
        break;
    case INTEGER64:
        rc = exi_basetypes_encoder_integer_64(&stream, value64);
        print_wire(rc, &stream);
        break;
    case INTEGER32:
        rc = exi_basetypes_encoder_integer_32(&stream, value32);
        print_wire(rc, &stream);
        break;
    case FROM_SIGNED64:
        rc = exi_basetypes_decoder_signed(&stream, &signed_value);
        if (rc == 0) {
            rc = exi_basetypes_convert_64_from_signed(&signed_value, &value64);
        }
        printf("rc=%d value=%" PRId64 "\n", rc, value64);
        break;
    case FROM_SIGNED32:
        rc = exi_basetypes_decoder_signed(&stream, &signed_value);
        if (rc == 0) {
            rc = exi_basetypes_convert_from_signed(&signed_value, &value32, max_octets);
        }
        printf("rc=%d value=%" PRId32 "\n", rc, value32);
        break;
    case DECODE_INTEGER64:
        rc = exi_basetypes_decoder_integer_64(&stream, &value64);
        printf("rc=%d value=%" PRId64 "\n", rc, value64);
        break;
    case DECODE_INTEGER32:
        rc = exi_basetypes_decoder_integer_32(&stream, &value32);
        printf("rc=%d value=%" PRId32 "\n", rc, value32);
        break;
    case PARTS: {
        int sign = 0;
        uint64_t magnitude = 0;
        rc = exi_basetypes_decoder_bool(&stream, &sign);
        if (rc == 0) {
            rc = exi_basetypes_decoder_uint_64(&stream, &magnitude);
        }
        if (rc != 0) {
            fprintf(stderr, "parts decode failed: %d\n", rc);
            return 1;
        }
        printf("sign=%d magnitude=%" PRIu64 "\n", sign, magnitude);
        break;
    }
    }
    return 0;
}
