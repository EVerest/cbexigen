#pragma once

#include <cstddef>
#include <cstdint>
#include <gtest/gtest.h>
#include <iomanip>
#include <optional>
#include <span>
#include <string>

template <typename HeaderT, size_t Len>
inline void setHeader(HeaderT& header, const uint8_t (&sessionID)[Len], uint64_t timeStamp,
                      const std::optional<decltype(header.Signature)>& signature = std::nullopt) {
    static_assert(Len >= 8, "SessionID must be size 8. Larger is allowed for string literal \\0 term");
    header.SessionID.bytesLen = 8;
    std::copy(&sessionID[0], &sessionID[0] + 8, header.SessionID.bytes);
    header.TimeStamp = timeStamp;
    header.Signature_isUsed = false;
    if (signature) {
        throw std::runtime_error("not supported yet");
    }
}
template <typename HeaderT>
inline bool assertHeader(const HeaderT& header, const uint8_t* sessionID, uint64_t timeStamp) {
    bool success = false;
    [&]() {
        ASSERT_EQ(header.SessionID.bytesLen, 8);
        ASSERT_EQ(memcmp(header.SessionID.bytes, sessionID, 8), 0);
        ASSERT_EQ((int)header.Signature_isUsed, 0);
        ASSERT_EQ(header.TimeStamp, timeStamp);
        success = true;
    }();
    return success;
}
#define ASSERT_ISO20_HEADER_EQ(...)                                                                                    \
    do { /* NOLINT */                                                                                                  \
        if (!assertHeader(__VA_ARGS__)) {                                                                              \
            return;                                                                                                    \
        }                                                                                                              \
    } while (0) /* NOLINT */
#define ASSERT_ISO20_STREQ(str, sv)                                                                                    \
    do { /* NOLINT */                                                                                                  \
        std::string_view svv = sv;                                                                                     \
        ASSERT_EQ((str).charactersLen, svv.size());                                                                    \
        ASSERT_EQ((str).characters, svv);                                                                              \
    } while (0) /* NOLINT */

template <typename StrT>
inline void setString(StrT& out, std::string_view in) {
    out.charactersLen = in.size();
    std::copy(in.begin(), in.end(), out.characters);
}

template <typename StrT>
inline void setBytes(StrT& out, std::span<uint8_t> in) {
    out.bytesLen = in.size();
    std::copy(in.begin(), in.end(), out.bytes);
}

template <typename It>
std::string toHexStr(It begin, It end, std::string_view delimit = "\\x") {
    std::stringstream ss;
    auto it = begin;
    for (; it != end; ++it) {
        ss << delimit << std::setfill('0') << std::setw(2) << std::hex << (uint16_t)*it;
    }
    return std::move(ss).str();
}
