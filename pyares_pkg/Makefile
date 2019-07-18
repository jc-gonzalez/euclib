#
# Helpful commands for packaging 
#
# This makefile only concerns packaging and building.
# To be used only if you plan to build your own packages
# for different target platforms
#

clean:
	rm -rf pyares.egg-info/ build/
	@echo "Cleaning eventual __pycache__ directories"
	find pyares/ -name "__pycache__"  -type d -exec rm -r "{}" \; > /dev/null 2>&1

build: clean
	@echo " ----- Building universal wheel package"
	python setup.py bdist_wheel
	@echo " ----- built pyares: $(grep version setup.py)"

test:
	pytest -v tests
