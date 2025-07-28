from pathlib import Path

import os
import subprocess
from google.protobuf import descriptor_pb2


def generate_service_block(services):
    lines = []
    fn_counter = 0
    for s_index, svc in enumerate(services):
        function_names = []
        for func in svc["functions"]:
            input_cols = [
                f'new column_descriptor_impl({i}, "{col["name"]}", type_kind_type::{col["type"]})'
                for i, col in enumerate(func["input"])
            ]
            output_cols = [
                f'new column_descriptor_impl({i}, "{col["name"]}", type_kind_type::{col["type"]})'
                for i, col in enumerate(func["output"])
            ]

            lines.append(
                f'        auto input_{fn_counter} = new record_descriptor_impl({{{", ".join(input_cols)}}});'
            )
            lines.append(
                f'        auto output_{fn_counter} = new record_descriptor_impl({{{", ".join(output_cols)}}});'
            )

            lines.append(
                f"        auto fn_{fn_counter} = new function_descriptor_impl("
                f'{fn_counter}, "{func["name"]}", function_kind_type::{func["kind"]}, '
                f"input_{fn_counter}, output_{fn_counter});"
            )
            function_names.append(f"fn_{fn_counter}")
            fn_counter += 1

        lines.append(
            f'        auto service_{s_index} = new service_descriptor_impl("{svc["name"]}", '
            f'{{{", ".join(function_names)}}});'
        )
        lines.append(f"        services_.push_back(service_{s_index});\n")
    return "\n".join(lines)


def parse_services_from_proto(proto_path):
    desc_path = "tmp_descriptor.pb"
    subprocess.run(
        [
            "protoc",
            f"--proto_path={os.path.dirname(proto_path)}",
            f"--descriptor_set_out={desc_path}",
            "--include_imports",
            os.path.basename(proto_path),
        ],
        check=True,
    )

    with open(desc_path, "rb") as f:
        data = f.read()

    file_set = descriptor_pb2.FileDescriptorSet()
    file_set.ParseFromString(data)

    services = []
    for file_desc in file_set.file:
        for service in file_desc.service:
            service_dict = {"name": service.name, "functions": []}
            for method in service.method:
                func_dict = {
                    "name": method.name,
                    "kind": "Unary",
                    "input": [{"name": "arg", "type": "Int4"}],  #
                    "output": [{"name": "result", "type": "String"}],  #
                }
                service_dict["functions"].append(func_dict)
            services.append(service_dict)

    os.remove(desc_path)
    return services


def render_template(template_path: str, output_path: str, context: dict):
    with open(template_path, "r") as f:
        template = f.read()

    for key, value in context.items():
        template = template.replace(f"{{{{ {key} }}}}", value)

    with open(output_path, "w") as f:
        f.write(template)


if __name__ == "__main__":
    proto_file = "proto/greeter.proto"
    services = parse_services_from_proto(proto_file)

    service_def_block = generate_service_block(services)
    render_template(
        template_path="templates/plugin_api_impl.template.cpp",
        output_path="plugin_api_impl.cpp",
        context={"service_definitions": service_def_block},
    )

    print("plugin_api_impl.cpp generated from .proto")
