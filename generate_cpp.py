import os
import subprocess
from google.protobuf import descriptor_pb2

PROTOBUF_TYPE_MAP = {
    1: "Double",
    2: "Float",
    3: "Int64",
    4: "UInt64",
    5: "Int32",
    6: "Fixed64",
    7: "Fixed32",
    8: "Bool",
    9: "String",
    10: "Group",
    11: "Message",
    12: "Bytes",
    13: "UInt32",
    14: "Enum",
    15: "SFixed32",
    16: "SFixed64",
    17: "SInt32",
    18: "SInt64",
}

PROTOBUF_TO_PLUGIN_TYPE = {
    "Int32": "Int4",
    "Int64": "Int8",
    "String": "String",
    "Bool": "Bool",
    "Bytes": "Bytes",
    "Double": "Float8",
    "Float": "Float4",
}


def extract_message_type_map(file_set):
    type_map = {}
    for file_desc in file_set.file:
        pkg = file_desc.package
        for msg in file_desc.message_type:
            fq_name = f".{pkg}.{msg.name}" if pkg else f".{msg.name}"
            type_map[fq_name] = msg
    return type_map


def extract_fields(descriptor, type_map):
    fields = []
    for field in descriptor.field:
        if field.type == field.Type.TYPE_MESSAGE:
            nested_desc = type_map.get(field.type_name)
            if nested_desc:
                nested_fields = extract_fields(nested_desc, type_map)
                fields.extend(nested_fields)  # flatten
            else:
                fields.append({"name": field.name, "type": "Message"})
        else:
            proto_type = PROTOBUF_TYPE_MAP.get(field.type, "Unknown")
            plugin_type = PROTOBUF_TO_PLUGIN_TYPE.get(proto_type, "Unknown")
            fields.append({"name": field.name, "type": plugin_type})
    return fields


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
    os.remove(desc_path)

    type_map = extract_message_type_map(file_set)

    services = []
    for file_desc in file_set.file:
        for service in file_desc.service:
            svc_dict = {"name": service.name, "functions": []}
            for method in service.method:
                input_desc = type_map.get(method.input_type)
                output_desc = type_map.get(method.output_type)
                input_fields = (
                    extract_fields(input_desc, type_map) if input_desc else []
                )
                output_fields = (
                    extract_fields(output_desc, type_map) if output_desc else []
                )

                func_dict = {
                    "name": method.name,
                    "kind": (
                        "Unary"
                        if not method.client_streaming and not method.server_streaming
                        else "Streaming"
                    ),
                    "input": input_fields,
                    "output": output_fields,
                }
                svc_dict["functions"].append(func_dict)
            services.append(svc_dict)

    return services


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

    print(" plugin_api_impl.cpp generated from .proto")
