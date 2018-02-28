.PHONY: start start_armhf start_aarch64

start:
	docker run -v ${PWD}/app:/app  -it --rm --link crossbar crossbario/autobahn-python

start_armhf:
	docker run -v ${PWD}/app:/app  -it --rm --link crossbar crossbario/autobahn-python-armhf

start_aarch64:
	docker run -v ${PWD}/app:/app  -it --rm --link crossbar crossbario/autobahn-python-aarch64
