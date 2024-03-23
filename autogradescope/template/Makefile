.PHONY: autograder
autograder: test
	mkdir -p _build/autograder
	cd _build/autograder && cp -r ../../setup/* .
	cd _build/autograder && cp -r ../../data/* .
	cp tests/*.py _build/autograder
	if [[ -f requirements.txt ]]; then cat requirements.txt >> _build/autograder/requirements.txt; fi
	cd _build/autograder && zip -r autograder.zip * && mv autograder.zip ..

.PHONY: test
test:
	rm -rf _build/test
	mkdir -p _build/test
	cd _build/test && cp -r ../../setup/* .
	cd _build/test && cp -r ../../data/* .
	cp tests/*.py _build/test
	cp solution/* _build/test
	cd _build/test && pytest -s


.PHONY: clean
clean:
	rm -rf _build
