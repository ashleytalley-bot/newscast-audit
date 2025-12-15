.PHONY: setup render open clean

setup:
	./scripts/setup_venv.sh

render:
	source .venv/bin/activate && quarto render opex-newscast-audit.qmd

open:
	open opex-newscast-audit.html

clean:
	rm -f opex-newscast-audit.html
