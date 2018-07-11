.PHONY: build clean test

build:
	pyinstaller wizard.spec -y

clean:
	rm -rf build dist

test:
	pytest --cov=app
