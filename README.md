# Flatland

Flatland is a library that allows you to create a virtual 2-D environment in
which you can put and move one or more virtual sensors to get virtual range
measures.

Moving the sensors into this virtual space (really a plan) you can study how 
to implement your 
[SLAM](https://en.wikipedia.org/wiki/Simultaneous_localization_and_mapping) 
or navigation algorithms.

The name Flatland is after the romance
["Flatland: A Romance of Many Dimensions"](https://en.wikipedia.org/wiki/Flatland)
by  Edwin Abbott Abbott.

This romance describes a flat world populated by geometric figures that live
and act as persons.

## Install

### 0. Install Python and Git

In order to use Flatland package and read its complete documentation you must first install Python and Git application on your operating system.

#### Python 3.x installation

The Flatland package requires a Python version >= 3.5

**Linux** users can install Python directly from their distribution packages.

**Windows** users can download and install Python 3.x from [official site](https://www.python.org/downloads/windows/)

#### Git installation

**Windows** users can follow the instruction on the [official site](https://gitforwindows.org/) 

**Linux Debian flavored** users can run `apt-get install git`

**Linux other flavours** users can install it from their package manager.


### 1. Create a dedicated virtual environment

```python
  python3 -m venv flatland
```



### 2. Move into the virtual environment and clone this repository

To clone a git repository you have first to move into the flatland directory and type the commands

```
  cd flatland
  git clone https://github.com/Saruccio/Flatland.git
```

This will end up in a Flatland folder to appear in your virtual environment directory.

### 3. Install prerequisite using *pip*

#### 3.1 Activate flatland virtualenv
Move into the virtual environment and activate it

**Windows**

```
  cd flatland
  Script\activate
```

**Linux**
```
  cd flatland
  source bin/activate
```

this will ensure that all packages will be installed into the virtual environment without polluting the global (or external) Python runtime environment.

#### 3.2 Install prerequisite

In oreder to make simpler the prerequisite installation, all prerequisite have been listed into the file '''requirements.txt''' into the Flatland directory.
  To install prerequisite type
  
```
   cd flatland
   pip install -r Flatland/requirements.txt
```
 
### 4. Build the documentation

The documentation is written using the [Sphinx](http://www.sphinx-doc.org/en/master/) and you can build the last release in html format issuing following commands

```
cd Flatland\docs 
make html
```

When build completes you che read the documentation loading the file `Flatland/docs/build/html/index.html` in a browser.









