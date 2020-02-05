
2-Way Partial Dependency
========================

This project demonstrates a 2-way partial dependency using DataRobot python API.

## Dependencies
 
You will need a DataRobot account and access to a dedicated prediction server.

You will need the python batch scoring script (used to score the variations efficiently).

```
pip install -U datarobot_batch_scoring
```

You will also need a bunch of python libraries, including the DataRobot API

```
pip install chardet
pip install numpy
pip install pandas
pip install datarobot
```

You will need create the CONFIG file and fill in the required details from the deployed model.

```
cp config.yml.example config.yml
vi config.yml
```

## About

The core functions that create the partial dependencies are found 
inside the file [PartialDependency.py](PartialDependency.py). 

These functions are used by the example script and the web application example.

## Caveats

The 3D plotting functions will fail if the features used are not numerical.
TODO: Add support for categoricals. 


## Usage

The script [Example.py](Example.py) Shows you how to create the partial dependency in a standalone python script.

This script will generate a plot like the one below.

![2 Way Partial Dependency for Insurance Fraud](scripts/Example.png "Insurance Fraud Partial Dependency" )


The file [app.py](app.py) and the contents of the [templates](templates) directory is a python flask 
web application you can use to generate 2 way partial dependency plots for any pair of numerical features 
used in a DataRobot model.

It will store the plots generated in the folder [static](static) so that they do not need to be re-generated.


To run:

```
python app.py
```

Then follow the prompts



