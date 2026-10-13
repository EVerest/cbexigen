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
    TO_SIGNED64, TO_SIGNED32, INTEGER64, INTEGER32, SIGNED_BYTES,
    TO_UNSIGNED64, TO_UNSIGNED32, ENCODE_UINT8, ENCODE_UINT16, ENCODE_UINT32, ENCODE_UINT64,
    FROM_SIGNED64, FROM_SIGNED32, DECODE_INTEGER64, DECODE_INTEGER32, PARTS,
    UINT8, UINT16, UINT32, UINT64, FROM_UNSIGNED32, FROM_UNSIGNED64,
    DECODE_UNSIGNED64, DECODE_UNSIGNED32, UNSIGNED_BYTES
};

static const struct {
    const char* name;
    enum operation operation;
    int argc;
} operations[] = {
    {"to_unsigned64", TO_UNSIGNED64, 3},
    {"to_unsigned32", TO_UNSIGNED32, 4},
    {"decode_unsigned64", DECODE_UNSIGNED64, 3},
    {"decode_unsigned32", DECODE_UNSIGNED32, 4},
    {"unsigned_bytes", UNSIGNED_BYTES, 3},
    {"to_signed64", TO_SIGNED64, 3},
    {"to_signed32", TO_SIGNED32, 4},
    {"integer64", INTEGER64, 3},
    {"integer32", INTEGER32, 3},
    {"signed_bytes", SIGNED_BYTES, 4},
    {"from_signed64", FROM_SIGNED64, 3},
    {"from_signed32", FROM_SIGNED32, 4},
    {"decode_integer64", DECODE_INTEGER64, 3},
    {"decode_integer32", DECODE_INTEGER32, 3},
    {"parts", PARTS, 3},
    {"encode_uint8", ENCODE_UINT8, 3},
    {"encode_uint16", ENCODE_UINT16, 3},
    {"encode_uint32", ENCODE_UINT32, 3},
    {"encode_uint64", ENCODE_UINT64, 3},
    {"uint8", UINT8, 3},
    {"uint16", UINT16, 3},
    {"uint32", UINT32, 3},
    {"uint64", UINT64, 3},
    {"from_unsigned32", FROM_UNSIGNED32, 4},
    {"from_unsigned64", FROM_UNSIGNED64, 3},
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
    uint8_t unsigned8 = 123;
    uint16_t unsigned16 = 12345;
    uint32_t unsigned32 = 123456789;
    uint64_t unsigned64 = 123456789;
    exi_unsigned_t unsigned_value = {0};
    exi_signed_t signed_value = {0};
    exi_bitstream_t stream;
    int rc = 0;

    if (op >= FROM_SIGNED64 || op == SIGNED_BYTES) {
        const char* hex = argv[op == SIGNED_BYTES ? 3 : 2];
        uint8_t* destination = op == SIGNED_BYTES ? signed_value.data.octets : bytes;
        size_t capacity = op == SIGNED_BYTES ? sizeof(signed_value.data.octets) : sizeof(bytes);
        size_t hex_length = strlen(hex);
        if (hex_length % 2 != 0 || hex_length / 2 > capacity) {
            return 2;
        }
        for (size_t i = 0; i < hex_length / 2; i++) {
            char pair[3] = {hex[2 * i], hex[2 * i + 1], 0};
            char* end;
            unsigned long byte = strtoul(pair, &end, 16);
            if (end != pair + 2 || byte > 255) {
                return 2;
            }
            destination[i] = (uint8_t)byte;
        }
        if (op == SIGNED_BYTES) {
            if (strcmp(argv[2], "0") != 0 && strcmp(argv[2], "1") != 0) {
                return 2;
            }
            signed_value.is_negative = argv[2][0] == '1';
            signed_value.data.octets_count = hex_length / 2;
        } else {
            length = hex_length / 2;
        }
    } else if (op >= TO_UNSIGNED64 && op <= ENCODE_UINT64) {
        unsigned64 = strtoumax(argv[2], NULL, 10);
    } else {
        value64 = strtoimax(argv[2], NULL, 10);
        value32 = (int32_t)value64;
    }
    exi_bitstream_init(&stream, bytes, length, 0, NULL);

    if (op == FROM_UNSIGNED32 || op == FROM_UNSIGNED64) {
        if (length > sizeof(unsigned_value.octets)) {
            return 2;
        }
        memcpy(unsigned_value.octets, bytes, length);
        unsigned_value.octets_count = length;
    }

    switch (op) {
    case TO_UNSIGNED64:
    case TO_UNSIGNED32:
        rc = op == TO_UNSIGNED64 ?
            exi_basetypes_convert_64_to_unsigned(&unsigned_value, unsigned64) :
            exi_basetypes_convert_to_unsigned(&unsigned_value, (uint32_t)unsigned64, max_octets);
        if (rc == 0) {
            rc = exi_basetypes_encoder_unsigned(&stream, &unsigned_value);
        }
        print_wire(rc, &stream);
        break;
    case DECODE_UNSIGNED64:
    case DECODE_UNSIGNED32:
        rc = exi_basetypes_decoder_unsigned(&stream, &unsigned_value);
        if (rc == 0) {
            rc = op == DECODE_UNSIGNED64 ?
                exi_basetypes_convert_64_from_unsigned(&unsigned_value, &unsigned64) :
                exi_basetypes_convert_from_unsigned(&unsigned_value, &unsigned32, max_octets);
        }
        printf("rc=%d value=%" PRIu64 "\n", rc,
               op == DECODE_UNSIGNED64 ? unsigned64 : (uint64_t)unsigned32);
        break;
    case UNSIGNED_BYTES:
        rc = exi_basetypes_decoder_unsigned(&stream, &unsigned_value);
        printf("rc=%d count=%zu bytes=", rc, unsigned_value.octets_count);
        for (size_t i = 0; i < unsigned_value.octets_count; i++) {
            printf("%02x", unsigned_value.octets[i]);
        }
        putchar('\n');
        break;
    case ENCODE_UINT8:
        rc = exi_basetypes_encoder_uint_8(&stream, (uint8_t)unsigned64);
        print_wire(rc, &stream);
        break;
    case UINT8:
        rc = exi_basetypes_decoder_uint_8(&stream, &unsigned8);
        printf("rc=%d value=%" PRIu8 "\n", rc, unsigned8);
        break;
    case ENCODE_UINT16:
        rc = exi_basetypes_encoder_uint_16(&stream, (uint16_t)unsigned64);
        print_wire(rc, &stream);
        break;
    case UINT16:
        rc = exi_basetypes_decoder_uint_16(&stream, &unsigned16);
        printf("rc=%d value=%" PRIu16 "\n", rc, unsigned16);
        break;
    case ENCODE_UINT32:
        rc = exi_basetypes_encoder_uint_32(&stream, (uint32_t)unsigned64);
        print_wire(rc, &stream);
        break;
    case UINT32:
        rc = exi_basetypes_decoder_uint_32(&stream, &unsigned32);
        printf("rc=%d value=%" PRIu32 "\n", rc, unsigned32);
        break;
    case ENCODE_UINT64:
        rc = exi_basetypes_encoder_uint_64(&stream, (uint64_t)unsigned64);
        print_wire(rc, &stream);
        break;
    case UINT64:
        rc = exi_basetypes_decoder_uint_64(&stream, &unsigned64);
        printf("rc=%d value=%" PRIu64 "\n", rc, unsigned64);
        break;
    case FROM_UNSIGNED32:
        rc = exi_basetypes_convert_from_unsigned(&unsigned_value, &unsigned32, max_octets);
        printf("rc=%d value=%" PRIu32 "\n", rc, unsigned32);
        break;
    case FROM_UNSIGNED64:
        rc = exi_basetypes_convert_64_from_unsigned(&unsigned_value, &unsigned64);
        printf("rc=%d value=%" PRIu64 "\n", rc, unsigned64);
        break;
    case SIGNED_BYTES:
        rc = exi_basetypes_encoder_signed(&stream, &signed_value);
        print_wire(rc, &stream);
        break;
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
