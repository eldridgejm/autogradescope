.PHONY: autograder
autograder: clean
	rm -rf ../autogradescope/__pycache__
	mkdir -p _build/autograder
	cp test_submission.py conftest.py _build/autograder
	cp --dereference -r autogradescope _build/autograder/
	cp -r gradescope_setup/* _build/autograder
	cd _build/autograder && zip -r autograder.zip * && mv autograder.zip ..

.PHONY: clean
clean:
	rm -rf _build
