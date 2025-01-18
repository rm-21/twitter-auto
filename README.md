# How to use?
I am presuming you have a Linux enviroment running somewhere.

* Run `make` in a terminal. You will require `poetry` as your package manager.
* Run the command: 
```bash 
poetry run python -m twitter_auto -e '<email>' -u '<username>' -p '<password>' -f '<file_loc>'
```
* Ensure there is an empty line at the end of the `.txt` file. If the account in the file still exists, it should subscribe to it.

