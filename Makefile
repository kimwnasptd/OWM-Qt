
default: clean
	@echo "Ready!"

clean:
	find Files/* -type d -exec rm -rv {} + 
	find . -name "settings.ini" -delete
	find . -name "paths.pkl" -delete
	touch settings.ini
