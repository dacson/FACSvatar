.PHONY: start start_armhf start_aarch64

start:
	docker run -v ${PWD}/app:/app  -it --rm --link crossbar crossbario/autobahn-python
# python /usr/local/bin/pip install pandas
#  --dns 8.8.8.8

start_armhf:
	docker run -v ${PWD}/app:/app  -it --rm --link crossbar crossbario/autobahn-python-armhf

start_aarch64:
	docker run -v ${PWD}/app:/app  -it --rm --link crossbar crossbario/autobahn-python-aarch64
