#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <exi_v2gtp.h>
#include <iso20_CommonMessages_Decoder.h>
#include <iso20_CommonMessages_Encoder.h>

#include "../test_header_utils.hpp"

class Test_SessionSetup : public testing::Test {
protected:
    uint8_t m_data[256] = {0};
    exi_bitstream_t m_stream;
};

/** \param xml_input (that was used to generate the EXI binary using EXIficient)
 * <?xml version="1.0" encoding="UTF-8"?>
 * <ns0:SessionSetupReq xmlns:ns0="urn:iso:std:iso:15118:-20:CommonMessages">
 *   <ns1:Header xmlns:ns1="urn:iso:std:iso:15118:-20:CommonTypes">
 *     <ns1:SessionID>3030303030303030</ns1:SessionID>
 *     <ns1:TimeStamp>1707896956850052</ns1:TimeStamp>
 *   </ns1:Header>
 *   <ns0:EVCCID>PIXV12345678901231</ns0:EVCCID>
 * </ns0:SessionSetupReq>
 */
TEST_F(Test_SessionSetup, WhenEncodingKnownSessionSetupRequest_ThenResultMatchesExpected) {
    static constexpr uint8_t expected[] =
        "\x01\xFE\x80\x02\x00\x00\x00\x28" //<- header
        "\x80\x8c\x04\x18\x18\x18\x18\x18\x18\x18\x18\x08\x49\xfb\x4f\xba\xba\xa8\x40\x32\x0a\x28\x24\xac\x2b\x18\x99"
        "\x19\x9a\x1a\x9b\x1b\x9c\x1c\x98\x18\x99\x19\x98\x80";
    static constexpr size_t streamLen = 0x28;
    exi_bitstream_init(&m_stream, m_data, sizeof(m_data), 8, NULL);
    iso20_exiDocument exiDoc = {};
    exiDoc.SessionSetupReq_isUsed = 1;
    uint8_t sessionID[] = "\x30\x30\x30\x30\x30\x30\x30\x30";
    setHeader(exiDoc.SessionSetupReq.Header, sessionID, 1707896956850052);
    setString(exiDoc.SessionSetupReq.EVCCID, "PIXV12345678901231");

    int res = encode_iso20_exiDocument(&m_stream, &exiDoc);
    size_t len = exi_bitstream_get_length(&m_stream);
    V2GTP20_WriteHeader(&m_data[0], len, V2GTP20_MAINSTREAM_PAYLOAD_ID);

    ASSERT_EQ(res, 0);
    ASSERT_EQ(len, streamLen);
    ASSERT_EQ(memcmp(m_data, expected, sizeof(expected) - 1), 0)
        << std::string("\\x") << toHexStr(m_data, m_data + sizeof(expected) - 1, "\\x") << '\n'
        << std::string("\\x") << toHexStr(&expected[0], &expected[0] + sizeof(expected) - 1, "\\x");
}

TEST_F(Test_SessionSetup, WhenDecodingKnownSessionSetupRequest_ThenResultMatchesExpected) {
    uint8_t input[] =
        "\x01\xFE\x80\x02\x00\x00\x00\x28" //<- header
        "\x80\x8c\x04\x18\x18\x18\x18\x18\x18\x18\x18\x08\x49\xfb\x4f\xba\xba\xa8\x40\x32\x0a\x28\x24\xac\x2b\x18\x99"
        "\x19\x9a\x1a\x9b\x1b\x9c\x1c\x98\x18\x99\x19\x98\x80";
    iso20_exiDocument exiDoc = {};
    exi_bitstream_init(&m_stream, &input[0], sizeof(input), 8, NULL);
    uint32_t len = 0;

    int res = V2GTP20_ReadHeader(&input[0], &len, V2GTP20_MAINSTREAM_PAYLOAD_ID);
    ASSERT_EQ(res, 0);
    res = decode_iso20_exiDocument(&m_stream, &exiDoc);
    ASSERT_EQ(res, 0);

    static constexpr size_t streamLen = 0x28;
    ASSERT_EQ(len, streamLen);
    ASSERT_EQ((int)exiDoc.SessionSetupReq_isUsed, 1);
    static const uint8_t sessionID[] = "\x30\x30\x30\x30\x30\x30\x30\x30";
    ASSERT_ISO20_HEADER_EQ(exiDoc.SessionSetupReq.Header, sessionID, 1707896956850052);
    ASSERT_ISO20_STREQ(exiDoc.SessionSetupReq.EVCCID, "PIXV12345678901231");
}
