# The Perfect Prefect documentation

Here is the hosted Github page: https://matt9993.github.io/prefect-docs-page/



## Prerequisites
```
Python

Graphviz library in any way graphviz library installed on your system/host machine that builds the documentation.

    e.g. apt-get install graphviz -y
```

## Docs folder
This folder contains everything to generate the final document about the flows.

## first-flows.rst file
Dedicated to the first example Prefect flow documentation page in the project.


## second-flows.rst file
Dedicated to the second custom dbt processes Prefect flow documentation page in the project.

## utils.rst file
Holds all the util functions used for this project with the example flows.

## src/pipelines folde
Keeps all the prefect flow files.

## src/common folde
Keeps all the putil function files.

## How to use the prefecttask project for the docs
It is a standalone github repo, because this package is still very new and there is no way to install it with pip install. 
At least for me it failed with the error message saying no version for package.

So I cloned the repo and installed it with the
```
python setup.py install
```
command to the virtual env. And after that you can use the README file in the
repository to find out how to use this.
https://github.com/sphinx-contrib/prefecttask


## Sphinx docs
The base folder for the documentations with Sphinx project initialised were generated in the
```
sp-docs
```

Then after creating the rst files (still in sp-docs), the following command was used to generate the actual html docs.
```
sphinx-build -b html . ../docs
```


## Updating the docs github page
1.) First option
After the docs were generated/updated from the sp-docs folder to the docs folder a git push was executed
to update the files in the repository.

2.) Second option
An automated github action is available in the repo but the .nojekyll file was added manually because the
pipeline is not able to copy the .nojekyll file the branch in the end.


## Special thanks
Huge thanks for the 2 opensource github projects that were used to create the Prefect docs.

1.) An extension to autodoc Prefect Tasks: https://github.com/sphinx-contrib/prefecttask

2.) An extension to add Prefect flow visualizations into you Sphinx documentation.:
    https://github.com/sphinx-contrib/prefectviz
