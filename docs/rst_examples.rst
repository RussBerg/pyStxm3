

##################
    RST Examples
##################

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**box's around text**

Download the ``.zip`` or ``.msi`` for your architecture (64-bit is preferable if your machine supports it).


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
**hint::**

.. hint::

   By default, each screen layout 'remembers' the last :doc:`scene </data_system/scenes/introduction>`
   it was used on. Selecting a different screen layout will switch to the layout **and** jump to that scene.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**note::**

.. note::

   There are a few corner cases where :kbd:`LMB` is used for selection.
   For example, the :doc:`File Browser </editors/file_browser/introduction>`.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**over ride a doc title**

:doc:`Scan Selection Tools </interface/window_system/scan_plugins/tools/index>`

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**tip::**

.. tip:: Dealing with Different Sizes

   Dealing with different sized images and different sized outputs is tricky.
   If you have a mis-match between the size of the input image and the render output size,
   the VSE will try to auto-scale the image to fit it entirely in the output.
   This may result in clipping. If you do not want that, use *Crop* and/or *Offset* in the Input
   panel to move and select a region of the image within the output. When you use *Crop* or *Offset*,
   the auto-scaling will be disabled and you can manually re-scale by adding the Transform effect.


^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**admonition:: Reference**

.. admonition:: Reference
   :class: refbox

   :Menu:      :menuselection:`View --> Toggle Maximize Area`
   :Hotkey:    :kbd:`Ctrl-Up`, :kbd:`Shift-Spacebar`

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   
**list-table::**

.. list-table::
   :widths: 15 85

   * - :kbd:`RMB`
     - To select an item.
   * - :kbd:`Shift-RMB`
     - To add more items to the selection.
   * - :kbd:`LMB`
     - To perform an action on the selection.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Hyperlink**

Video: `Learn more about Blender's Mouse Button usage <https://vimeo.com/76335056>`__.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**:kbd:**

- :kbd:`Ctrl-C` -- Over any :ref:`ui-operation-buttons` copies their Python command into the clipboard.

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**code-block::**

   .. code-block:: python
      :linenos:

      import bpy
      def some_function():
          ...

^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. sidebar:: Sidebar Title
   :subtitle: Optional Sidebar Subtitle

   Subsequent indented lines comprise
   the body of the sidebar, and are
   interpreted as body elements.
   
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^