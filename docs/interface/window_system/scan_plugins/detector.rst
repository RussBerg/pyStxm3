*************
Detector Scan
*************

.. figure:: /resources/images/scan_plugins/scan_plugins_detector.png


The Detector scan is used to center the detector XY stages in the center of the beam.

To perform a Detector scan:

	1 - Ensure that the sample is completely out of the way.

	2 - Ensure that the OSA is completely out of the way by sending it to +3500um.

	3 - Select the **Detector Scan** tab.

	4 - Using the 2D selection tool, select an area aprrox 1500x1500um on the screen centered around (0, 0).
	**The scan region can also be set by entering the center and range for X and Y in the fields on the Detector Scan pane.**

	5 - With the center and range set, enter the number of points or step size for each X and Y in the **# Points** or **Step** fields for X and Y	on the Detector Scan panel.

	6 - Press the **Start** button on the **Scan Control** pane.

.. figure:: /resources/images/scan_plugins/scan_plugins_detector_scan.png

	Yellow box in plot indicates the region to be scanned, 
	the center and range were set by clicking and dragging 
	the 2D selection tool

When the scan has completed the data will be saved in todays data directory and a thumbnail will appear in the **Data** pane.

.. figure:: /resources/images/scan_plugins/scan_plugins_detector_scan_data_pane.png

	Detector scan saved as file C180524006



Setting Detector Center
-----------------------

Now to set the detector center, click with the :kbd:`LMB` on the image then press and hold :kbd:`Ctrl-C` for **Center** and move the mouse over the image of the detector scan guiding it to the center of the detector. 
As you do this the **Center Pos** for X and Y will change to the mouse values so that when you are at the center of the detector on the image the center values will match those, 
then press the **Set Detector Center** button on the Detector Scan pane. When you click the button the detector XY stages will move to the selected new center and once there, reset their 
positions to 0.

.. figure:: /resources/images/scan_plugins/scan_plugins_detector_scan_wdata.png

The detector is now centered, smokem if ya gottem