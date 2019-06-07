
##################
  Scan Plugins
##################

.. image:: /resources/images/image7.png
	:scale: 80 %


The Scans tab contains the results of what the system found in the
**scan\_plugins** sub directory of
**cls.applications.pystxm**. The display order (from top to
bottom) of the scans is determined in code by an ID number so that
when loaded the order from top to bottom can be controlled. In
this case the order of the scans is designed to go from Alignment
type scans to Data collection and Data Collection refinement
scans. Each scan has some combination of center and range along
with dwell time in order to conduct the scan in the desired
manner, some scans have extra features/buttons to make the scan
more convenient.

Functions common to all scans is the ability to
reload a previous scan with the **Load Scan** button as well if
the user **right clicks** the mouse they will get a sub menu
that will allow them to load or save other options **if that scan
allows them**, some menu options will be disabled because they
have no meaning for that particular scan.

.. container:: tocdescr

      .. container:: descr

         .. image:: /resources/images/image8.png
            :align: center

         Right click sub menu, here the scan allows all options to be enabled

      .. container:: descr

         .. image:: /resources/images/image9.png
            :align: center

         Here the scan does not allow for an energy specification so it is disabled

..  note::

    As well, the graphical tools for selecting the scan region are
    located on the **Image** tab of the data visualization pane, the
    selection tools are dynamically enabled or disabled depending on
    the currently selected scan.

.. figure:: /resources/images/image10.png
    :align: center

    Scan Selection Tools

.. figure:: /resources/images/tools/image11.png
    :align: left

How to do ROI Selections for scans
==================================

:doc:`Scan Selection Tools </interface/window_system/scan_plugins/tools/index>`


All possible scans are located on the Scans tab. The order in which they appear is
from top: scans relating to alignment to bottom: scans relating to data collection 
and data refinement.

.. note:: Scan Modes
		
	When the scan tab bar contains the follwing statement **[DISABLED by scanning mode]**
	that means that this particular scan is not supported in the current scanning mode which is 
	one of the 3 following scanning modes:
	
		1 - COARSE SAMPLEFINE
			The sample is positioned by the Coarse XY stages and the SampleFine XY piezo stages mounted on the coarse stage.
			Raster scanning for fine scans is done my scanning the SampleFine XY piezo stages.
			
		2 - COARSE ZONEPLATE
			The sample is positioned by the Coarse XY stages and the scanning is done by raster scanning the Zoneplate XY piezo stages.
			
		3 - GONI ZONEPLATE
			The sample is positioned by the Goniometer XYZ stages and the scanning is done by raster scanning the Zoneplate XY piezo stages.


.. toctree::
   :maxdepth: 2

   /interface/window_system/scan_plugins/detector.rst
   /interface/window_system/scan_plugins/osa.rst
   /interface/window_system/scan_plugins/osa_focus.rst
   /interface/window_system/scan_plugins/coarse_image.rst
   /interface/window_system/scan_plugins/coarse_goni.rst
   /interface/window_system/scan_plugins/fine_image.rst 
   /interface/window_system/scan_plugins/tomography.rst
   /interface/window_system/scan_plugins/focus.rst
   /interface/window_system/scan_plugins/point.rst
   /interface/window_system/scan_plugins/line.rst
   /interface/window_system/scan_plugins/positioner.rst