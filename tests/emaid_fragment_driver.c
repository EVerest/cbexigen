/* SPDX-License-Identifier: Apache-2.0 */
/*
 * Copyright (C) 2022 - 2026 chargebyte GmbH
 * Copyright (C) 2022 - 2026 Contributors to EVerest
 */

/*
 * Encodes one ISO 15118-2 eMAID element fragment and prints it as hex.
 *
 * Deliberately compiles against both the old and the new generated API: the
 * struct member names Id and CONTENT are the same either way, and the
 * presence flags only exist once the element fragment grammar is generated.
 *
 * usage: emaid_fragment_driver <Id> <eMAID value>
 */
#include <stdio.h>
#include <string.h>

#include "exi_bitstream.h"
#include "exi_error_codes.h"
#include "iso2_msgDefDatatypes.h"
#include "iso2_msgDefEncoder.h"

static void set_string(char* dest, uint16_t* len, size_t capacity, const char* src) {
    size_t n = strlen(src);
    if (n + 1 > capacity) {
        fprintf(stderr, "value of %zu chars exceeds capacity %zu\n", n, capacity);
        n = 0;
    }
    memcpy(dest, src, n);
    dest[n] = '\0';
    *len = (uint16_t)n;
}

int main(int argc, char** argv) {
    uint8_t buffer[1024];
    exi_bitstream_t stream;
    struct iso2_exiFragment fragment;
    size_t length;
    int error;

    if (argc != 3) {
        fprintf(stderr, "usage: %s <Id> <eMAID value>\n", argv[0]);
        return 2;
    }

    memset(buffer, 0, sizeof(buffer));
    exi_bitstream_init(&stream, buffer, sizeof(buffer), 0, NULL);

    init_iso2_exiFragment(&fragment);
    fragment.eMAID_isUsed = 1u;
    set_string(fragment.eMAID.Id.characters, &fragment.eMAID.Id.charactersLen,
               sizeof(fragment.eMAID.Id.characters), argv[1]);
    set_string(fragment.eMAID.CONTENT.characters, &fragment.eMAID.CONTENT.charactersLen,
               sizeof(fragment.eMAID.CONTENT.characters), argv[2]);
#ifdef ISO2_HAS_ELEMENT_FRAGMENT_GRAMMAR
    fragment.eMAID.Id_isUsed = 1u;
    fragment.eMAID.CONTENT_isUsed = 1u;
#endif

    error = encode_iso2_exiFragment(&stream, &fragment);
    if (error != EXI_ERROR__NO_ERROR) {
        fprintf(stderr, "encode failed: %d\n", error);
        return 1;
    }

    length = exi_bitstream_get_length(&stream);
    for (size_t i = 0; i < length; i++) {
        printf("%02x", buffer[i]);
    }
    printf("\n");

    return 0;
}
