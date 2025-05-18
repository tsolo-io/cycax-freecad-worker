
build:
	cd docker-freecad
	docker build -t tsolo.io/local/tsolo-freecad:1.0 .
	cd ..
	cp ../dist/cycax-freecad-worker.sh .
	docker build -t cycax_freecad_worker:1.0.0-0 .

checkout:
	git clone https://github.com/jaecktec/docker-freecad || true
	cd docker-freecad
	git pull

