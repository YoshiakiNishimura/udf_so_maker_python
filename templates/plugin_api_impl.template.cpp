#include "plugin_api.h"
namespace udf {
class column_descriptor_impl : public column_descriptor {
public:
    column_descriptor_impl(index_type i, std::string_view n, type_kind_type k)
        : idx(i), name(n), kind(k) {}
    index_type index() const noexcept override { return idx; }
    std::string_view column_name() const noexcept override { return name; }
    type_kind_type type_kind() const noexcept override { return kind; }

private:
    index_type idx;
    std::string_view name;
    type_kind_type kind;
};

class record_descriptor_impl : public record_descriptor {
public:
    record_descriptor_impl(std::vector<column_descriptor*> c) : cols(std::move(c)) {}
    const std::vector<column_descriptor*>& columns() const noexcept override { return cols; }

private:
    std::vector<column_descriptor*> cols;
};

class function_descriptor_impl : public function_descriptor {
public:
    function_descriptor_impl(index_type i, std::string_view n, function_kind_type k,
                             record_descriptor_impl* in, record_descriptor_impl* out)
        : idx(i), name(n), kind(k), input(in), output(out) {}
    index_type function_index() const noexcept override { return idx; }
    std::string_view function_name() const noexcept override { return name; }
    function_kind_type function_kind() const noexcept override { return kind; }
    const record_descriptor& input_record() const noexcept override { return *input; }
    const record_descriptor& output_record() const noexcept override { return *output; }

private:
    index_type idx;
    std::string_view name;
    function_kind_type kind;
    record_descriptor_impl* input;
    record_descriptor_impl* output;
};

class service_descriptor_impl : public service_descriptor {
public:
    service_descriptor_impl(std::string_view n, std::vector<function_descriptor*> f)
        : name(n), funcs(std::move(f)) {}
    std::string_view service_name() const noexcept override { return name; }
    const std::vector<function_descriptor*>& functions() const noexcept override { return funcs; }

private:
    std::string_view name;
    std::vector<function_descriptor*> funcs;
};

class plugin_api_impl : public plugin_api {
public:
    plugin_api_impl() {
{{ service_definitions }}
    }

    const std::vector<service_descriptor*>& services() const noexcept override {
        return services_;
    }

private:
    std::vector<service_descriptor*> services_;
};

extern "C" plugin_api* create_plugin_api() {
    return new plugin_api_impl();
}
}
