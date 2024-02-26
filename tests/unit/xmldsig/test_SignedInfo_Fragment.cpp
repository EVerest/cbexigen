#include <gmock/gmock.h>
#include <gtest/gtest.h>

#include <iso2_msgDefEncoder.h>
#include <iso20_DC_Encoder.h>
#include <iso20_AC_Encoder.h>

#include <cstring>

template <typename XmlFragmentDocT>
class Test_SignedInfo_Fragment : public testing::Test {
protected:
    using Document_t = XmlFragmentDocT;
    uint8_t m_data[512] = {0};
    exi_bitstream_t m_stream;
    int encode_xmldsigFragment(exi_bitstream_t* stream, Document_t*);
    template <typename StrT>
    static void setExiStr(StrT& out, std::string_view setStr)
    {
        out.charactersLen = setStr.length();
        memcpy(out.characters, setStr.data(), setStr.length());
    }
    template <typename StrT, size_t Len>
    static void setExiArr(StrT& out, const uint8_t (&setStr)[Len])
    {
        out.bytesLen = Len - 1;
        memcpy(out.bytes, setStr, Len - 1);
    }
};
class Test_SignedInfo_Fragment_ISO2: public Test_SignedInfo_Fragment<iso2_xmldsigFragment> {
protected:
    int encode_xmldsigFragment(exi_bitstream_t* stream, Document_t* document)
    {
        return encode_iso2_xmldsigFragment(stream, document);
    }
};



/** \brief Fragment encode
 * \param xml_input
 * <?xml version="1.0" encoding="UTF-8"?>
 * <ns0:SignedInfo xmlns:ns0="http://www.w3.org/2000/09/xmldsig#">
 *   <ns0:CanonicalizationMethod Algorithm="http://www.w3.org/TR/canonical-exi/"/>
 *   <ns0:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha512"/>
 *   <ns0:Reference URI="id1">
 *     <ns0:Transforms>
 *       <ns0:Transform Algorithm="http://www.w3.org/TR/canonical-exi/"/>
 *     </ns0:Transforms>
 *     <ns0:DigestMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha512"/>
 *     <ns0:DigestValue>AQIDBAUGBw==</ns0:DigestValue>
 *   </ns0:Reference>
 *   <ns0:Reference URI="id2">
 *     <ns0:Transforms>
 *       <ns0:Transform Algorithm="http://www.w3.org/TR/canonical-exi/"/>
 *     </ns0:Transforms>
 *     <ns0:DigestMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha512"/>
 *     <ns0:DigestValue>AQIDBAUGBw==</ns0:DigestValue>
 *   </ns0:Reference>
 * </ns0:SignedInfo>
 */
TEST_F(Test_SignedInfo_Fragment_ISO2, WhenEncodingKnownSupportedAppProtocolRequest_ThenResultMatchesExpected) {
    static constexpr uint8_t expected[] =
        "\x80\x81\x12\xb4\x3a\x3a\x38\x1d\x17\x97\xbb\xbb\xbb\x97\x3b\x99\x97\x37\xb9\x33\x97\xaa\x29\x17\xb1\xb0\xb7"
        "\x37\xb7\x34\xb1\xb0\xb6\x16\xb2\xbc\x34\x97\xa1\xab\x43\xa3\xa3\x81\xd1\x79\x7b\xbb\xbb\xb9\x73\xb9\x99\x73"
        "\x7b\x93\x39\x79\x91\x81\x81\x89\x79\x81\xa1\x7b\xc3\x6b\x63\x23\x9b\x4b\x39\x6b\x6b\x7b\x93\x29\x1b\x2b\x1b"
        "\x23\x9b\x09\x6b\x9b\x43\x09\xa9\x89\x92\x20\x56\x96\x43\x10\x25\x68\x74\x74\x70\x3a\x2f\x2f\x77\x77\x77\x2e"
        "\x77\x33\x2e\x6f\x72\x67\x2f\x54\x52\x2f\x63\x61\x6e\x6f\x6e\x69\x63\x61\x6c\x2d\x65\x78\x69\x2f\x48\x6a\xd0"
        "\xe8\xe8\xe0\x74\x5e\x5e\xee\xee\xee\x5c\xee\x66\x5c\xde\xe4\xce\x5e\x64\x60\x60\x62\x5e\x60\x68\x5e\xf0\xda"
        "\xd8\xc8\xe6\xd2\xce\x5a\xda\xde\xe4\xca\x46\xca\xc6\xc8\xe6\xc2\x5a\xe6\xd0\xc2\x6a\x62\x64\x80\xe0\x20\x40"
        "\x60\x80\xa0\xc0\xe0\x81\x5a\x59\x0c\x80\x95\xa1\xd1\xd1\xc0\xe8\xbc\xbd\xdd\xdd\xdc\xb9\xdc\xcc\xb9\xbd\xc9"
        "\x9c\xbd\x51\x48\xbd\x8d\x85\xb9\xbd\xb9\xa5\x8d\x85\xb0\xb5\x95\xe1\xa4\xbd\x21\xab\x43\xa3\xa3\x81\xd1\x79"
        "\x7b\xbb\xbb\xb9\x73\xb9\x99\x73\x7b\x93\x39\x79\x91\x81\x81\x89\x79\x81\xa1\x7b\xc3\x6b\x63\x23\x9b\x4b\x39"
        "\x6b\x6b\x7b\x93\x29\x1b\x2b\x1b\x23\x9b\x09\x6b\x9b\x43\x09\xa9\x89\x92\x03\x80\x81\x01\x82\x02\x83\x03\x8d"
        "\xc0";
    static constexpr std::string_view c_canonMethodAlgorithm = "http://www.w3.org/TR/canonical-exi/";
    static constexpr std::string_view c_transformAlgorithm = "http://www.w3.org/TR/canonical-exi/";
    static constexpr std::string_view c_digestAlgorithm = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha512";
    static constexpr std::string_view c_signatureMethodAlgorithm = "http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha512";
    static constexpr const uint8_t c_digestValue[] = "\x01\x02\x03\x04\x05\x06\x07";
    static constexpr std::string_view c_refURI1 = "id1";
    static constexpr std::string_view c_refURI2 = "id2";
    static constexpr size_t streamLen = sizeof(expected) - 1;

    exi_bitstream_init(&m_stream, m_data, sizeof(m_data), 0, NULL);
    Document_t exiDoc = {};
    memset(&exiDoc, 0, sizeof(exiDoc));
    exiDoc.SignedInfo_isUsed = 1;
    auto& signInfo = exiDoc.SignedInfo;
    signInfo.Id_isUsed = 0;
    setExiStr(signInfo.CanonicalizationMethod.Algorithm, c_canonMethodAlgorithm);
    setExiStr(signInfo.SignatureMethod.Algorithm, c_signatureMethodAlgorithm);
    signInfo.Reference.arrayLen = 2;

    auto& ref1 = signInfo.Reference.array[0];
    ref1.URI_isUsed = 1;
    setExiStr(ref1.URI, c_refURI1);
    ref1.Transforms_isUsed = 1;
    setExiStr(ref1.Transforms.Transform.Algorithm, c_transformAlgorithm);
    setExiStr(ref1.DigestMethod.Algorithm, c_digestAlgorithm);
    setExiArr(ref1.DigestValue, c_digestValue);

    auto& ref2 = signInfo.Reference.array[1];
    ref2.URI_isUsed = 1;
    setExiStr(ref2.URI, c_refURI2);
    ref2.Transforms_isUsed = 1;
    setExiStr(ref2.Transforms.Transform.Algorithm, c_transformAlgorithm);
    setExiStr(ref2.DigestMethod.Algorithm, c_digestAlgorithm);
    setExiArr(ref2.DigestValue, c_digestValue);

    int res = encode_xmldsigFragment(&m_stream, &exiDoc);
    int len = exi_bitstream_get_length(&m_stream);

    ASSERT_EQ(res, 0);
    ASSERT_EQ(len, streamLen);
    const auto memcpyRes = memcmp(m_data, expected, sizeof(expected) - 1);
    ASSERT_EQ(memcpyRes, 0);
}
