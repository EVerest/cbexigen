#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <appHand_Decoder.h>
#include <appHand_Encoder.h>
#include <exi_v2gtp.h>

class Test_SupportedAppProtocol : public testing::Test {
protected:
    uint8_t m_data[256] = {0};
    exi_bitstream_t m_stream;
};

static void setProtocol(appHand_AppProtocolType& protoc, std::string_view ns, uint32_t vMaj, uint32_t vMin,
                        uint8_t schemaID, uint8_t priority) {
    protoc.ProtocolNamespace.charactersLen = ns.size();
    std::copy(ns.begin(), ns.end(), protoc.ProtocolNamespace.characters);
    protoc.VersionNumberMajor = vMaj;
    protoc.VersionNumberMinor = vMin;
    protoc.SchemaID = schemaID;
    protoc.Priority = priority;
}

/** \param xml input:
 * <?xml version="1.0" encoding="UTF-8"?>
 * <ns4:supportedAppProtocolReq xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 * xmlns:ns3="http://www.w3.org/2001/XMLSchema" xmlns:ns4="urn:iso:15118:2:2010:AppProtocol"> <AppProtocol>
 *         <ProtocolNamespace>urn:iso:15118:2:2010:MsgDef</ProtocolNamespace>
 *         <VersionNumberMajor>1</VersionNumberMajor>
 *         <VersionNumberMinor>0</VersionNumberMinor>
 *         <SchemaID>1</SchemaID>
 *         <Priority>1</Priority>
 *     </AppProtocol>
 *     <AppProtocol>
 *         <ProtocolNamespace>urn:din:70121:2012:MsgDef</ProtocolNamespace>
 *         <VersionNumberMajor>1</VersionNumberMajor>
 *         <VersionNumberMinor>0</VersionNumberMinor>
 *         <SchemaID>2</SchemaID>
 *         <Priority>2</Priority>
 *     </AppProtocol>
 *     <AppProtocol>
 *         <ProtocolNamespace>urn:iso:std:iso:15118:-20:DC</ProtocolNamespace>
 *         <VersionNumberMajor>1</VersionNumberMajor>
 *         <VersionNumberMinor>0</VersionNumberMinor>
 *         <SchemaID>3</SchemaID>
 *         <Priority>3</Priority>
 *     </AppProtocol>
 * </ns4:supportedAppProtocolReq>
 */
TEST_F(Test_SupportedAppProtocol, WhenEncodingKnownSupportedAppProtocolRequest_ThenResultMatchesExpected) {
    static constexpr uint8_t expected[] =
        "\x01\xFE\x80\x01\x00\x00\x00\x66" //<-header
        "\x80\x00\xeb\xab\x93\x71\xd3\x4b\x9b\x79\xd1\x89\xa9\x89\x89\xc1\xd1\x91\xd1\x91\x81\x89\x81\xd2\x6b\x9b\x3a"
        "\x23\x2b\x30\x01\x00\x00\x04\x00\x01\xb7\x57\x26\xe3\xa6\x46\x96\xe3\xa3\x73\x03\x13\x23\x13\xa3\x23\x03\x13"
        "\x23\xa4\xd7\x36\x74\x46\x56\x60\x02\x00\x00\x10\x08\x03\xce\xae\x4d\xc7\x4d\x2e\x6d\xe7\x4e\x6e\x8c\x87\x4d"
        "\x2e\x6d\xe7\x46\x26\xa6\x26\x27\x07\x45\xa6\x46\x07\x48\x88\x60\x04\x00\x00\x30\x21";
    static constexpr size_t streamLen = 0x66;
    static constexpr std::string_view namespaceISO15118_2 = "urn:iso:15118:2:2010:MsgDef";
    static constexpr std::string_view namespaceDin70121 = "urn:din:70121:2012:MsgDef";
    static constexpr std::string_view namespaceISO15118_20 = "urn:iso:std:iso:15118:-20:DC";
    exi_bitstream_init(&m_stream, m_data, sizeof(m_data), 8, NULL);
    appHand_exiDocument exiDoc = {};
    exiDoc.supportedAppProtocolReq_isUsed = 1;
    exiDoc.supportedAppProtocolReq.AppProtocol.arrayLen = 3;
    setProtocol(exiDoc.supportedAppProtocolReq.AppProtocol.array[0], namespaceISO15118_2, 1, 0, 1, 1);
    setProtocol(exiDoc.supportedAppProtocolReq.AppProtocol.array[1], namespaceDin70121, 1, 0, 2, 2);
    setProtocol(exiDoc.supportedAppProtocolReq.AppProtocol.array[2], namespaceISO15118_20, 1, 0, 3, 3);

    int res = encode_appHand_exiDocument(&m_stream, &exiDoc);
    int len = exi_bitstream_get_length(&m_stream);
    V2GTP_WriteHeader(m_data, len);

    ASSERT_EQ(res, 0);
    ASSERT_EQ(len, streamLen);
    ASSERT_EQ(memcmp(m_data, expected, sizeof(expected) - 1), 0);
}

TEST_F(Test_SupportedAppProtocol, WhenDecodingKnownSupportedAppProtocolRequestStream_ThenResultMatchesExpected) {
    uint8_t input[] =
        "\x01\xFE\x80\x01\x00\x00\x00\x66" //<-header
        "\x80\x00\xeb\xab\x93\x71\xd3\x4b\x9b\x79\xd1\x89\xa9\x89\x89\xc1\xd1\x91\xd1\x91\x81\x89\x81\xd2\x6b\x9b\x3a"
        "\x23\x2b\x30\x01\x00\x00\x04\x00\x01\xb7\x57\x26\xe3\xa6\x46\x96\xe3\xa3\x73\x03\x13\x23\x13\xa3\x23\x03\x13"
        "\x23\xa4\xd7\x36\x74\x46\x56\x60\x02\x00\x00\x10\x08\x03\xce\xae\x4d\xc7\x4d\x2e\x6d\xe7\x4e\x6e\x8c\x87\x4d"
        "\x2e\x6d\xe7\x46\x26\xa6\x26\x27\x07\x45\xa6\x46\x07\x48\x88\x60\x04\x00\x00\x30\x21";
    exi_bitstream_init(&m_stream, input, sizeof(input), 8, NULL);
    appHand_exiDocument exiDoc = {};
    uint32_t len = 0;

    int res = V2GTP_ReadHeader(input, &len);
    ASSERT_EQ(res, 0);
    res = decode_appHand_exiDocument(&m_stream, &exiDoc);
    ASSERT_EQ(res, 0);

    static constexpr size_t streamLen = 0x66;
    static constexpr std::string_view namespaceISO15118_2 = "urn:iso:15118:2:2010:MsgDef";
    static constexpr std::string_view namespaceDin70121 = "urn:din:70121:2012:MsgDef";
    static constexpr std::string_view namespaceISO15118_20 = "urn:iso:std:iso:15118:-20:DC";
    ASSERT_EQ(len, streamLen);
    ASSERT_EQ((int)exiDoc.supportedAppProtocolReq_isUsed, 1);
    ASSERT_EQ(exiDoc.supportedAppProtocolReq.AppProtocol.arrayLen, 3);

    auto& protoc0 = exiDoc.supportedAppProtocolReq.AppProtocol.array[0];
    ASSERT_EQ(protoc0.ProtocolNamespace.charactersLen, namespaceISO15118_2.size());
    ASSERT_EQ(memcmp(protoc0.ProtocolNamespace.characters, namespaceISO15118_2.data(), namespaceISO15118_2.size()), 0);
    ASSERT_EQ(protoc0.VersionNumberMajor, 1);
    ASSERT_EQ(protoc0.VersionNumberMinor, 0);
    ASSERT_EQ(protoc0.SchemaID, 1);
    ASSERT_EQ(protoc0.Priority, 1);

    auto& protoc1 = exiDoc.supportedAppProtocolReq.AppProtocol.array[1];
    ASSERT_EQ(protoc1.ProtocolNamespace.charactersLen, namespaceDin70121.size());
    ASSERT_EQ(memcmp(protoc1.ProtocolNamespace.characters, namespaceDin70121.data(), namespaceDin70121.size()), 0);
    ASSERT_EQ(protoc1.VersionNumberMajor, 1);
    ASSERT_EQ(protoc1.VersionNumberMinor, 0);
    ASSERT_EQ(protoc1.SchemaID, 2);
    ASSERT_EQ(protoc1.Priority, 2);

    auto& protoc2 = exiDoc.supportedAppProtocolReq.AppProtocol.array[2];
    ASSERT_EQ(protoc2.ProtocolNamespace.charactersLen, namespaceISO15118_20.size());
    ASSERT_EQ(memcmp(protoc2.ProtocolNamespace.characters, namespaceISO15118_20.data(), namespaceISO15118_20.size()),
              0);
    ASSERT_EQ(protoc2.VersionNumberMajor, 1);
    ASSERT_EQ(protoc2.VersionNumberMinor, 0);
    ASSERT_EQ(protoc2.SchemaID, 3);
    ASSERT_EQ(protoc2.Priority, 3);
}

/** \param xml input:
 * <?xml version="1.0" encoding="UTF-8"?>
 * <ns4:supportedAppProtocolRes
 *         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 *         xmlns:ns3="http://www.w3.org/2001/XMLSchema"
 *         xmlns:ns4="urn:iso:15118:2:2010:AppProtocol">
 *     <ResponseCode>OK_SuccessfulNegotiation</ResponseCode>
 *     <SchemaID>1</SchemaID>
 * </ns4:supportedAppProtocolRes>
 */
TEST_F(Test_SupportedAppProtocol, WhenEncodingKnownSupportedAppProtocolResponse_ThenResultMatchesExpected) {
    static constexpr uint8_t expected[] = "\x01\xfe\x80\x01\x00\x00\x00\x04" //<-header
                                          "\x80\x40\x00\x40";

    static constexpr size_t streamLen = 0x04;
    exi_bitstream_init(&m_stream, m_data, sizeof(m_data), 8, NULL);
    appHand_exiDocument exiDoc = {};
    exiDoc.supportedAppProtocolRes_isUsed = 1;
    exiDoc.supportedAppProtocolRes.SchemaID_isUsed = 1;
    exiDoc.supportedAppProtocolRes.SchemaID = 1;
    exiDoc.supportedAppProtocolRes.ResponseCode = appHand_responseCodeType_OK_SuccessfulNegotiation;

    int res = encode_appHand_exiDocument(&m_stream, &exiDoc);
    ASSERT_EQ(res, 0);
    int len = exi_bitstream_get_length(&m_stream);
    V2GTP_WriteHeader(m_data, len);

    ASSERT_EQ(len, streamLen);
    ASSERT_EQ(memcmp(m_data, expected, sizeof(expected) - 1), 0);
}
TEST_F(Test_SupportedAppProtocol, WhenDecodingKnownSupportedAppProtocolResponseStream_ThenResultMatchesExpected) {
    uint8_t input[] = "\x01\xfe\x80\x01\x00\x00\x00\x04" //<-header
                      "\x80\x40\x00\x40";
    exi_bitstream_init(&m_stream, input, sizeof(input), 8, NULL);
    appHand_exiDocument exiDoc = {};
    uint32_t len = 0;

    V2GTP_ReadHeader(input, &len);
    decode_appHand_exiDocument(&m_stream, &exiDoc);

    static constexpr size_t streamLen = 0x04;
    ASSERT_EQ(len, streamLen);
    ASSERT_EQ((int)exiDoc.supportedAppProtocolRes_isUsed, 1);
    ASSERT_EQ(exiDoc.supportedAppProtocolRes.ResponseCode, appHand_responseCodeType_OK_SuccessfulNegotiation);
    ASSERT_EQ((int)exiDoc.supportedAppProtocolRes.SchemaID_isUsed, 1);
    ASSERT_EQ(exiDoc.supportedAppProtocolRes.SchemaID, 1);
}
