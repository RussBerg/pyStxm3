******************
Data Visualization
******************

.. figure:: /resources/images/data_vis/data_vis_tabs.png
	:align: left
	
	Data vlisualization tabs

The data visualization area of the application is where the data is displayed as it arrives from the detector(s). It is
located in the center of the application so it is always in view for inspection as well as interaction by the user.



.. figure:: /resources/images/data_vis/data_vis_panel.png
	:align: center

	Data Visualization panel


The Data Visualization panel is separated into 3 different tabs:

    - Images

    - Spectra

    - Calibration Camera

	
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

======
Images
======

.. figure:: /resources/images/data_vis/data_vis_images.png
    :scale:	50 %
    :align: left

    Images tab showing the result of a Fine Image scan

.. admonition:: Mouse controls for the plot window
    :class: refbox

    :LeftBtn:    :kbd:`LMB` Selects images and shapes, drag handles of shapes to resize
    :MiddleBtn:  :kbd:`MMB` Click and drag to pan the image, click once to autoscale image
    :RightBtn:   :kbd:`RMB` Click and drag left and right to zoom the image

.. raw:: html

    <br><br><br><br><br>

When performing a 2D scan such as a Detector, OSA, Coarse or Fine Image scan, the data will
appear on the **Image** tab as the pixel data comes in.

The Images plot window is made up of
a central plot for displaying the actual data, 2 cross section plots on top and the right side
for showing cross section histogram data and a Contrast adjustment tool on the bottom of the
window.

Update Cross Sections
---------------------

.. figure:: /resources/images/data_vis/data_vis_alt_crosshair.png
    :scale:	50 %
    :align: left

    Crosshair visible when :kbd:`Alt` is pressed

.. admonition:: To update the plot cross sections
   :class: refbox

   :Hotkey:    :kbd:`Alt` hold it down and move mouse over image in plot window

.. raw:: html

    <br><br><br><br><br><br><br><br><br><br><br><br><br>

With an image visable in the plot window you can update the cross section plots by holding :kbd:`Alt`
down while moving the mouse over the image. When you do this there will be a cross hair displayed on
the plot and the cross sections will update to reflect where the cross hair is on the image.


Drag and Drop file loading
--------------------------

.. figure:: /resources/images/data_vis/data_vis_alt_img_drg_drp.png
    :scale:	75 %
    :align: center


    Load a previously collected dataset by dragging and dropping

Users can reload a dataset by dragging and dropping it onto the image plot. An example of when this
is handy is when you want to use a previous scan as the source for a new scan, you drag and drop the
previous scan on the screen then using the selection tools you would select the region of interest
for the new scan.

**Video of multiple drag and drop of images of different sizes, pan, zoom**

.. raw:: html

    <video width="640" height="480" controls src="dragdropzoom.mp4"></video>


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Spectra
=======

.. figure:: /resources/images/data_vis/data_vis_spec.png
    :scale:	50 %
    :align: left

    Spectra data loaded into spectra viewer

The Spectra tab contains a plot for viewing spectra data as it is being acquired or by dragging and
dropping it from the ThumbnailViewer widget. The scans that currently use the Spectra scan plotter are:

 - **Fine Point Scan** <LINK>
 - **Positioner Scan** <LINK>


It is pretty straight forward, as the points are collected during the scan they are plotted on the screen.

.. figure:: /resources/images/data_vis/data_vis_spec_lgnd.png
    :scale:	100 %
    :align: left

	Spectra plot trace legend

The name of the trace appears in a legend in the top left corner, the **nxStxm Nexus** <LINK HERE> file
format definition is the source of the naming convention **entry**, because there is only 1 trace in this
example it has the name **entry0**.

As with the images plot you can drag and drop spectra data from the **ThumbnailViewer** <LINK HERE> onto the
spectra plotter and it will load the data.

.. figure:: /resources/images/data_vis/data_vis_spec_multiple.png
    :scale:	40 %
    :align: left

	Spectra plot trace legend

If the scan contains multiple entry's then each entry will be assigned its own color and again the trace
name and color will be displayed in the legend.


.. raw:: html

    <br><br><br><br><br><br><br><br><br><br><br><br><br><br>

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Calibration Camera
==================

The purpose of the Calibration Camera tab is to quickly set the initial positions of the  following stages:

    - Zoneplate Z
    - OSA Z
    - Detector Z

.. figure:: /resources/images/data_vis/data_vis_calibcam_stages.png
    :scale:	100 %
    :align: left

	Calibration camera tab

The calibration camera is the view from a camera that is mounted on the top of the cryo-STXM tank and it is
looking down into the STXM through a viewport.

.. raw:: html

    <br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br><br>

The video image is used along with a measurement tool to set the positions of each stage.

.. figure:: /resources/images/data_vis/data_vis_calibcam_mtool.png
    :scale:	60 %
    :align: center


How to Calibrate
----------------

:1: Turn the high voltage power to **OFF** on the PMT
:2: Turn the light inside the tank to **ON**
:3: Get a frame of video by first pressing the **Grab Image** button, the frame of video will then be presented on the screen.
:4: Next decide where the sample holder is **as this will always be the 0 position** from which all other positions will be measured.
:5: Using the **Measurement Tool**, click on the location of the sample holder and drag towards the Zoneplate stopping when you get to the Zoneplate.

.. figure:: /resources/images/data_vis/data_vis_calibcam_cal_zp.png
    :scale:	80 %
    :align: center

    Click and drag to measure

.. figure:: /resources/images/data_vis/data_vis_calibcam_cal_zp_initpos.png
    :scale:	100 %
    :align: left

    Position of ZpZ before calibration

*In this example the measured position is 2543.44um, because the sample is the 0 position and the Zoneplate is upstream
of the sample the position for the Zoneplate is negative so the value that is entered into the Zoneplate Z field
is -2543.44*.

.. raw:: html

    <br><br><br><br><br><br>

:6: Enter the new value of Zoneplate Z into the Zoneplate Z field, when you change the value the background color of the field will change to blue indicating that the value is changed but not yet recorded, if you change focus to another widget before pressing :kbd:`Enter` the value in the field will return to the value before the change. In order to record the new value you must press :kbd:`Enter`, when you do the value wil be updated and the background color will return to white.

.. figure:: /resources/images/data_vis/data_vis_calibcam_cal_zp_val_2.png
    :scale:	100 %
    :align: left

    New value of Zoneplate Z entered into field

.. figure:: /resources/images/data_vis/data_vis_calibcam_cal_zp_val_3.png
    :scale:	100 %
    :align: center

    New value of Zoneplate Z after :kbd:`Enter` pressed

.. figure:: /resources/images/data_vis/data_vis_calibcam_cal_zp_val_4.png
    :scale:	100 %
    :align: center

    New value of Zoneplate Z has now been set to the calibrated value

:7: Calibrate OSA Z by clicking and dragging the left handle on the Measurement Tool and dragging it to the OSA Z position.
:8: Enter the value for OSA Z in teh OSA Z field, **again this will be a negative number** because the OSA Z stage is upstream of the sample.
:9: Now drag the left most handle of the Measurement Tool to the right to the tip of the Detector.
:10: Enter the value for Detector Z in teh Detector Z field **NOTE: this is now a positive value** because the Detector is downstream of the sample.

Calibration is now done.


.. raw:: html

    <br><br><br><br><br><br><br><br><br><br><br><br><br><br>
