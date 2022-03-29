# The Perfect Prefect documentation

## Docs folder
This folder contains everything to generate the final document about the flows.

## flows.rst file
Fill this in later


## Flows folder
Keeps all the prefect flow files.

## prefecttask folder
It is a standalone github repo, because this package is still very new and there is 
no way to install it with pip install. 
At least for me it failed with the error message saying no version for package.

So I cloned the repo and installed it with the
```
python setup.py install
```
command to the virtual env. And after that you can use the README file in the
repository to find out how to use this.
https://github.com/sphinx-contrib/prefecttask

