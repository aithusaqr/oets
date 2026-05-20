generate_protos:
	mkdir -p src/generated \
	protoc \
	  -I=../../proto \
	  --plugin=./node_modules/.bin/protoc-gen-ts_proto \
	  --ts_proto_out=src/generated \
	  --ts_proto_opt=esModuleInterop=true,forceLong=long,useOptionals=messages \
	  ../../proto/oets/common/*.proto \
	  ../../proto/oets/execution/*.proto


PHONY: generate_protos