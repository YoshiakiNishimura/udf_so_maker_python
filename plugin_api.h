#pragma once
#include <string_view>
#include <vector>
namespace udf {
enum class function_kind_type {
    Unary,
    ClientStreaming,
    ServerStreaming,
    BidirectionalStreaming,
};

enum class type_kind_type {
    Boolean,
    Int4,
    Int8,
    Decimal,
    Float4,
    Float8,
    String,
    Bytes,
    Timestamp,
    TimestampWithTimeZone,
    Blob,
    Clob
};

class column_descriptor {
  public:
    using index_type             = std::size_t;
    virtual ~column_descriptor() = default;

    virtual index_type index() const noexcept             = 0;
    virtual std::string_view column_name() const noexcept = 0;
    virtual type_kind_type type_kind() const noexcept     = 0;
};

class record_descriptor {
  public:
    virtual ~record_descriptor()                                            = default;
    virtual const std::vector<column_descriptor*>& columns() const noexcept = 0;
};

class function_descriptor {
  public:
    using index_type               = std::size_t;
    virtual ~function_descriptor() = default;

    virtual index_type function_index() const noexcept              = 0;
    virtual std::string_view function_name() const noexcept         = 0;
    virtual function_kind_type function_kind() const noexcept       = 0;
    virtual const record_descriptor& input_record() const noexcept  = 0;
    virtual const record_descriptor& output_record() const noexcept = 0;
};

class service_descriptor {
  public:
    virtual ~service_descriptor() = default;

    virtual std::string_view service_name() const noexcept                      = 0;
    virtual const std::vector<function_descriptor*>& functions() const noexcept = 0;
};

class plugin_api {
  public:
    virtual ~plugin_api()                                                     = default;
    virtual const std::vector<service_descriptor*>& services() const noexcept = 0;
};

extern "C" plugin_api* create_plugin_api();
} // namespace udf
