from pathlib import Path
from grpc_tools import protoc


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Your imports look like: import "common/source.proto";
# So the include root is the repo root.
PROTO_ROOT = PROJECT_ROOT

OUT_DIR = PROJECT_ROOT / "packages" / "python" / "src" / "oets_proto" / "generated"


def main() -> None:
    proto_files = sorted(
        path for path in PROTO_ROOT.glob("common/**/*.proto")
    )

    if not proto_files:
        raise FileNotFoundError(f"No .proto files found under {PROTO_ROOT / 'common'}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Project root: {PROJECT_ROOT}")
    print(f"Proto root:   {PROTO_ROOT}")
    print(f"Output dir:   {OUT_DIR}")

    print("Proto files:")
    for proto_file in proto_files:
        print(f"  - {proto_file.relative_to(PROTO_ROOT)}")

    args = [
        "grpc_tools.protoc",
        f"-I{PROTO_ROOT}",
        f"--python_out={OUT_DIR}",
        *[str(proto_file) for proto_file in proto_files],
    ]

    result = protoc.main(args)

    if result != 0:
        raise RuntimeError(f"protoc failed with exit code {result}")

    print(f"Generated {len(proto_files)} proto files into {OUT_DIR}")


if __name__ == "__main__":
    main()