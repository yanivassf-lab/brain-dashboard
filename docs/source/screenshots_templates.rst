Screenshots & Print Templates
=============================

Use these templates when capturing UI screens for the documentation or for quick reference sheets. Keep screenshots minimal, annotate with arrows/text and save as PNG.

Template: Admin - Run Processor
-------------------------------
Title: Admin - Run Processor
Description: Screen that shows the "Run processor" panel where an admin can trigger queued jobs.
Fields to capture:
- Timestamp visible in UI or log snippet
- Run list with selected run highlighted
- Buttons: Run now, Requeue, View logs

Template: User - Upload / New Run
---------------------------------
Title: New Run - Upload
Description: Screen showing upload form or the folder watcher status listing a newly detected dataset.
Fields to capture:
- Upload form elements (file picker, metadata fields)
- Success notification (example message)
- Link to run details

Template: Run Details / Logs
----------------------------
Title: Run Details
Description: Show run status, progress bar, and a short excerpt of the run log (first & last 5 lines).
Fields to capture:
- Run ID and timestamp
- Status (Queued / Running / Completed / Failed)
- Links to full log file and freesurfer output

Guidelines
----------
- Crop images to include only relevant UI.
- Avoid embedding secrets or long file paths in published documentation.
- Use consistent naming: admin_run_processor.png, user_upload.png, run_details.png

Export
------
- Use PNG for clarity. 1200×800 is a reasonable default for screenshots.
- For small reference cards, export 800×600 and add short captions.

Notes for adding to docs
-----------------------
- Add the screenshots to docs/_static/ and reference them from the appropriate pages with the Sphinx image directive.
- Example in RST:

.. code-block:: rst

   .. image:: _static/admin_run_processor.png
      :alt: Admin Run Processor
      :align: center

