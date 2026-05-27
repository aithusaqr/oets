ROOT := $(CURDIR)
OUT := $(CURDIR)/generated/python
PYTHON := python3

.PHONY: generate_python_protos clean_python_protos generate_python_services
# buf-based generation (preferred if `buf` is installed).
.PHONY: buf_generate buf_lint buf_breaking

PROTO_FILES := $(shell find $(ROOT)/common -name "*.proto" -type f)

SERVICE_PROTO_FILES := $(shell find $(ROOT)/common/services -name "*.proto" -type f)

generate_python_protos:
		rm -rf $(OUT)
	mkdir -p $(OUT)

	$(PYTHON) -m grpc_tools.protoc \
		-I $(ROOT) \
		--python_out=$(OUT) \
		--pyi_out=$(OUT) \
		$(PROTO_FILES)

	$(PYTHON) -m grpc_tools.protoc \
		-I $(ROOT) \
		--grpc_python_out=$(OUT) \
		$(SERVICE_PROTO_FILES)

	find $(OUT) -type d -exec touch {}/__init__.py \;


clean_python_protos:
	rm -rf $(OUT)/common

buf_generate:
	buf generate

buf_lint:
	buf lint

buf_breaking:
	buf breaking --against ".git#branch=main"
