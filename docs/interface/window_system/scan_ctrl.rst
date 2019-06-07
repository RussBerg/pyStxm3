
#########################
 Scan Control and Status
#########################

.. figure:: /resources/images/scan_ctrl_startup.png
	:scale: 75 %
	:align: center

	Scan control panel at startup

The Scan Control and Status pane is where the user controls the scan and monitors its progress and current status. 
It is comprised of several label widgets and buttons as well as a table that indicates the current scans file name(s)
as well as some meta data and current progress.

*******************************
Scan control and status widgets
*******************************

Scan Status Label
=================

The Scan status label indicates the current state of a scan, and will dynamically change its message to reflect
what is currently happening (scan wise).

.. container:: tocdescr

	.. container:: descr
		
		.. figure:: /resources/images/scan_ctrl_sts_lbl.png
			:scale: 100 %
		            
			Status label when scan is not running

	.. container:: descr
	
		.. figure:: /resources/images/scan_ctrl_sts_lbl_active.png
			:scale: 100 %
		         
			Status label during an active scan
		
	
.. figure:: /resources/images/scan_ctrl_sts_lbl_paused.png
	:scale: 100 %
	:align: center
	         
	Status label when scan is paused



Scan Control Buttons
====================

.. figure:: /resources/images/scan_ctrl_ctrl_btns.png
	:scale: 100 %
	:align: center

	Scan control buttons with Pause currently disabled

Pretty straight forward, they are buttons and they control the scan, depending on the current state of the scan a
button maybe enabled or disabled depending. For example, when a user clicks **Start** the Start button will be 
disabled and the Pause button will be enabled, the Start button will not become enabled again until the scan
has completed or been Stopped by the user.

Start a scan
============

.. figure:: /resources/images/scan_ctrl_active.png
	:scale: 75 %
	:align: center

	Scan control panel when scan is active

To start a scan that has been configured simply click the **Start** button on the
scan control and status panel. Once the scan is active, the status changes from **idle** to **Scanning...**
and remains that status until completed. When the scan is running the Start button will be disabled 
along with the fields in the **Scans** tab this is so that a user cannot inadvertantly try to 
start another scan while one is already running. Only 1 scan can be executed at a time.

Pause a scan
===========

.. figure:: /resources/images/scan_ctrl_paused.png
	:scale: 75 %
	:align: center

	Scan control panel when scan has been paused
	
To pause an active scan click the **Pause** button, the pause button will then show that it is depressed, 
a scan can only be paused right before it starts a new iteration of the scan which is not always the same 
for each scan so expect a short delay after pressing pause to wait for the scan to pause. The scan can be 
resumed by again pressing the pause button 


Stop a scan
===========

.. figure:: /resources/images/scan_ctrl_done.png
	:scale: 75 %
	:align: center

	Scan control panel when scan completed
	
To stop a scan click the **Stop** button, depending on how elaborate the scan is it may 
take several seconds for it to completely stop and the status to show **idle**.


Scan Time Indicators
====================
	
.. figure:: /resources/images/scan_ctrl_sts_time.png
	:scale: 100 %
	:align: center

	Elapsed and Estemated time labels
	
The Elapsed time will begin counting up from 00:00 once the scan has been started and will stop when it is completed.
The Estimated time label will indicate based on the current scan parameters approximately how long the scan should take.


Individual Scan Progress
========================
	
.. figure:: /resources/images/scan_ctrl_sts_indivscan.png
	:scale: 75 %
	:align: center

	Each scan gets its own detail, filename, current progress
	
When the user clicks **Start** on a new scan, a filename will be generated and added to the Individual scan progress table. 
The current state of the scan will change to active and the progress of the scan will be tracked by a progress bar on the same 
line in the table. For a stack or multi spatial fine image scan this table will show the progress of each frame of data as 
it is acquired.

.. figure:: /resources/images/scan_ctrl_sts_stack.png
	:scale: 65 %
	:align: center

	Status while executing a 40 eV stack
	

.. toctree::
   :maxdepth: 1




