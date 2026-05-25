ROOT := $(CURDIR)/common
OUT := $(CURDIR)/generated/python

PROTO_FILES := \
	$(ROOT)/*.proto \
	$(ROOT)/execution/*.proto \
	$(ROOT)/reconciliation/*.proto

generate_python_protos:
	rm -rf $(OUT) \
	PYTHONPATH=$(PYTHONPATH):$(ROOT):$(OUT) &&\
	mkdir -p $(OUT)
	protoc \
		-I $(CURDIR) \
		--python_out=$(OUT) \
		$(PROTO_FILES)
	touch $(OUT)/common/__init__.py
	touch $(OUT)/common/execution/__init__.py
	touch $(OUT)/common/reconciliation/__init__.py

clean_python_protos:
	rm -rf $(OUT)/common