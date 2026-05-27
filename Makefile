ROOT := $(CURDIR)/common
OUT := $(CURDIR)/generated/python

PROTO_FILES := \
	$(ROOT)/*.proto \
	$(ROOT)/execution/*.proto \
	$(ROOT)/reconciliation/*.proto

.PHONY: generate_python_protos clean_python_protos
# buf-based generation (preferred if `buf` is installed).
.PHONY: buf_generate buf_lint buf_breaking

generate_python_protos:
	rm -rf $(OUT)
	mkdir -p $(OUT)
	touch $(OUT)/__init__.py
	python -m grpc_tools.protoc \
		-I $(CURDIR) \
		--python_out=$(OUT) \
		$(PROTO_FILES)
	touch $(OUT)/common/__init__.py
	touch $(OUT)/common/execution/__init__.py
	touch $(OUT)/common/reconciliation/__init__.py

clean_python_protos:
	rm -rf $(OUT)

buf_generate:
	buf generate

buf_lint:
	buf lint

buf_breaking:
	buf breaking --against ".git#branch=main"
