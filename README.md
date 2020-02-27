# pyStxm
python Qt software for STXM data acquisition, this application was originally put together to preform data collection on the UHV STXM 
at the SM beam line (10ID1) at the CLS. The application uses several main frameworks to deliver the data collection capability, namely:
 
* Python 3.7, The open source programming used
* Qt5, The open source application framework used
* Epics, R3.14.12.4, The open source distributed control system
* BlueSky, 1.5.3, Bluesky Data Collection Framework 
* Synapps 5.7, The device and data collection software
* PyEpics 3, The connection to the DCS from the python side

  
There is a second part to this software and that is the SynApps Epics applications that provide the low level device control, namely:
	
- **motor**: to provide the positioner control


## Getting Started

This software is completely dependant on Epics for providing the connection to all positioners and counters as well as the engine for doing scans. When the software is started a connection is made to all configured devices and therefore the Epics side of the software must be running before attempting to start pyStxm.

At the time of authorship this repo is currently only available within the CLS.

### Prerequisites

The pyStxm software is dependent on the following python modules (note that their individual dependencies are not listed):

 - guidata (1.7.6)
 - guiqwt (3.0.3) with req'd modifications
 - h5py (2.6.0)
 - NeXpy (0.9.3)
 - nexusformat (0.4.5)
 - numpy (1.11.3)
 - pyepics (3.2.6)
 - PythonQwt (0.5.5)
 - QtPy (1.2.1)
 - bluesky (1.5.3)
 - ophyd (1.3.0)
 - databroker (0.12.2)
 - caproto (0.3.4)
 - suitcase (0.11.0)
 - scipy (0.18.1)
 - simplejson (3.10.0)
 - spyder (3.1.2)
 - Twisted (16.6.0)
 - Yapsy (1.11.223)
 - zope.interface (4.3.3)
  - pymongo (0.3.0)


### Installing

Start by creating a clone of the repo:

1. Create a directory to clone the repo

```C:\tmp\Feb21>git clone https://github.clsi.ca/bergr/pyStxm.git```

This will create a **pyStxm** directory with all of the software in it.

## Set environment 

set your **PYTHONPATH** variable to point to the directory that you  cloned the repo into


LINUX:

 - ```setenv PYTHONPATH <repo dir>/pyStxm```

WINDOWS:

- ```set PYTHONPATH=<repo dir>/pyStxm```

## Edit app.ini
Before the application can be started you must first edit some paths in the pyStxm/app.ini file.
This file is located in:
```<repo dir>/pyStxm/applications/pyStxm```

Under the section [DEFAULT]change **top** and **dataDir** to point to the correct location for your pyStxm, examples are show below:

```top = C://tmp//Feb21//pyStxm//cls//```

```dataDir = S://STXM-data//Cryo-STXM//2017```


## Create the guest data directory

Create a directory called **guest** in your data directory that you gave above in the app.ini file.

## Running a test 

You should now be able to cd to:

```<repo dir>/cls/applications/pyStxm```

and run pyStxm like this:

```>python stxmMain.py```


## Built With

* [Python](https://www.python.org/) - The open source programming used
* [Qt](https://www.qt.io/) - The open source application framework used
* [BlueSky] (https://nsls-ii.github.io/bluesky/) - Bluesky Data Collection Framework
* [Epics](http://www.aps.anl.gov/epics/) - The open source device and data acquisition control
* [Synapps] (https://www1.aps.anl.gov/bcda/synapps/) The device and data collection software the 


## Contributing

Please read [CONTRIBUTING.md](https://gist.github.com/PurpleBooth/b24679402957c63ec426) for details on our code of conduct, and the process for submitting pull requests to us.

## Versioning

For the versions available, see the [tags on this repository](https://github.com/your/project/tags). 

## Author

* **Russ Berg** -  [pyStxm](https://github.clsi.ca/bergr/pyStxm)



## License

This project is licensed under the GPL2 License - see the [LICENSE.md](LICENSE.md) file for details







