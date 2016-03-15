"""
Module: help.py
Defines the HTML code used in the help dialog of the KiWQM Field Data
Formatter application.

Title: Data & Procedures Officer
Organisation: DPI Water
Date modified: 13/10/2015
"""
page = r"""
<h1 id="kiwqm-field-data-importer-help">KiWQM Field Data Importer Help</h1>
<h2 id="introduction">Introduction</h2>
<p>Welcome to the <em>KiWQM Field Data Importer Help</em> file. This document briefly describes how to use the <em>Field Data Importer</em>, provides explanations of the various fields requiring user input, and defines the codes used.</p>
<h2 id="how-to-use-this-application">How to use this application</h2>
<p>KiWQM requires that any imported data is loaded in a specific format. The <em>KiWQM Field Data Importer</em> helps get your field data into that format easily. The application can be used to load data from a data logger file (such as that created by the Hydrolab instruments when measurements are saved in the field) or to input data collected manually on a <em>Water Sample Log</em>.</p>
<p>After starting the application, you will see the <em>Load screen</em> and should do the following:</p>
<ol style="list-style-type: decimal">
<li>Select the water quality instrument and turbiditimeter used for data collection from the drop-down lists of available instruments.</li>
<li>Select the sampler that collected the data.</li>
<li>Select the data entry mode:
<ol style="list-style-type: lower-alpha">
<li>If you are importing data from a data logger file, select <em>Load logger file</em>, and then click the <em>Browse</em> button to choose the file you wish to import.</li>
<li>If you are entering data manually, select <em>Manual data entry</em>.</li>
</ol></li>
<li>Press the <em>Continue</em> button. You will be taken to the data entry screen. If you have selected <em>Manual data entry</em> you will first be asked how many samples you are entering data for.</li>
<li>Enter the measurement details (e.g. measuring program, station number etc.) as described in the <a href="#description-of-fields">Description of fields</a> table below. Some of the fields require text, some fields are drop-down selections. The Sampling ID field is automatically generated once the <em>Station number</em> and <em>Date</em> have been entered. If you have imported data from a logger file, ensure that the dates, times and depths are consistent with the physical <em>Water Sample Log</em> sheet.</li>
<li>Once you have entered all the required data, press the <em>Export data</em> button at the bottom of the screen. If you have left any required fields empty, you will be prompted to complete those fields. Note that not <em>all</em> the fields are mandatory--see <a href="#description-of-fields">Description of fields</a> for details on mandatory and optional fields.</li>
<li>If you have imported data from a logger file, you will be asked to confirm that you have validated the dates, times and depths as recorded by the logger against the physical <em>Water Sample Log</em> sheet to ensure they are consistent. If you have not yet done this, go back and validate these parameters before exporting.</li>
<li>After the data has been exported, it is ready for importing to KiWQM. See the procedure <a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/32055.pdf"><em>Bulk Data Import into KiWQM Database</em> (STOP 32055)</a>.</li>
<li>If you need to start again, you can press the <em>Reset data</em> button to clear all data and go back to the first screen.</li>
</ol>
<h3 id="editing-data">Editing data</h3>
<p>Three buttons are provided in the data entry screen to facilitate easy data editing:</p>
<ul>
<li><em>Add row</em>: Adds a row to the list of data to be edited. This can be done after importing data from a logger or after going into manual mode. In such a way, manual and logger entries can be entered at the same time.</li>
<li><em>Delete row</em>: Deletes the selected row or rows in the data entry table. A single row can be selected by clicking with the mouse. Multiple rows can be selected by clicking a row with the mouse, holding down the <em>Shift</em> button on the keyboard, and then selecting the end of the data range by clicking the mouse or using the down arrow on the keyboard.</li>
<li><em>Copy down</em>: Allows values from one row to be copied down to other rows. This is useful for bulk editing of measuring program numbers, dates, times, location numbers, sequence numbers, matrix type, sample type, field officer and instrument. To use this function, select the source row at the top of the range along with the rows to copy to, then click the <em>Copy down</em> button. A dialog box will appear asking you to select the columns that you wish to copy. Tick the boxes you wish to copy, then click <em>OK</em>. The selected values from the top row will be copied down to the other rows.</li>
</ul>
<h2 id="description-of-fields">Description of fields<a name="description-of-fields"></a></h2>
<table border=1>
<colgroup>
<col width="23%" />
<col width="58%" />
<col width="17%" />
</colgroup>
<thead>
<tr class="header">
<th align="left">Field</th>
<th align="left">Definition</th>
<th align="left">Mandatory</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left"><p>MP# (Measuring program number)</p></td>
<td align="left"><p>The measuring program number assigned to the project in <em>KiWQM</em>. This is in the form <em>MP###</em>.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="even">
<td align="left"><p>Station#</p></td>
<td align="left"><p>A 6-8 digit identifier that specifies the monitoring station at which the sample was collected. See procedure <a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/32005.pdf"><em>Water quality project, sample, fraction and station numbers (product identification and traceability)</em> (STOP 32005)</a> for further information.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="odd">
<td align="left"><p>Sampling ID</p></td>
<td align="left"><p>The <em>sampling ID</em> is a unique identifier that is used to group samples collected together as part of a single sampling event. To ensure uniqueness, it is generated from the <em>station number</em> and the <em>date</em> in the format <em>STATION_NUMBER-YYMMDD</em>. These fields are described in more detail in <a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/32005.pdf"><em>STOP 32005: Water quality project, sample, fraction and station numbers (product identification and traceability)</em></a>.</p>
<p>Individual samples within the sampling are identified in conjunction with the <em>location number</em> and <em>sample sequence number</em> as described below. In most situations, a single sample will have a single <em>Sampling ID</em>.</p></td>
<td align="left"><p>Y (automatically generated)</p></td>
</tr>
<tr class="even">
<td align="left"><p>Date</p></td>
<td align="left"><p>The date the sampling event took place. The date can be input in any format as long as it contains two digits for day, two digits for month and two or four digits for year <em>in that order</em>. The date will be automatically reformatted to the format <em>DD/MM/YYYY</em> if it was not entered as such.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="odd">
<td align="left"><p>Time</p></td>
<td align="left"><p>The time at which the field measurements were taken or the sample was collected. The time can be entered in any format as long as it is entered in 24-hour time and contains at least two digits for hour and two digits for minute. The time can include seconds (two digits). The time will be automatically reformatted to the format <em>HH:MM:SS</em> (24-hour time). In general, the seconds should be zero so as to match the data exported by the laboratory. Where field measurements are taken using a data logger, the time recorded on the WSL should match the time recorded on the data logger. Since samples are often collected and bottled just after the field measurements are taken, the time recorded here may be slightly earlier than the exact time the sample was removed from the media or bottled.</p>
<p>The time recorded here <em>must match</em> the time recorded on the <em>Water Sample Log</em> filled at time of sample collection.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="even">
<td align="left"><p>Loc# (Location number)</p></td>
<td align="left"><p>A single-digit number used to separate samples from the same station and sampling event, but collected from different spatial locations. This is mostly relevant for groundwater samples where there could be multiple pipes at a single site, but is also relevant for surface water samples where spatial analysis of water quality at a particular station is important.</p>
<p>The <em>location number</em> starts at <em>1</em> and increments by one for each new location sampled. For groundwater samples, this column is used to indicate the <em>pipe number</em>. If only a single location or pipe exists at a station, this should be filled with a <em>1</em>.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="odd">
<td align="left"><p>Seq# (Sample sequence number)</p></td>
<td align="left"><p>A single-digit number used to specify individual samples within a sampling event at a given location. Every sample collected <em>must</em> have a <em>sequence number</em> associated with it. The <em>sequence number</em> starts at <em>1</em> and increments by one for each sample collected. For example, if three samples are collected at a station at different depths to form a depth profile, the first sample will have a <em>sequence number</em> of 1, the second sample will have a <em>sequence number</em> of 2, and the third sample will have a <em>sequence number</em> of 3. This also applies to replicate samples collected at a site. For example, a primary sample may have a <em>sequence number</em> of 1, while the replicate sample will have a <em>sequence number</em> of 2. If only one sample is collected at a station, it should be assigned a <em>sequence number</em> of <em>1</em>.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="even">
<td align="left"><p>Matrix</p></td>
<td align="left"><p>A two-letter code that describes the medium from which the sample was collected. This field must be populated with one of the acceptable values from the controlled list. Code definitions are provided in <a href="#matrix-codes">Code definitions</a> below.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="odd">
<td align="left"><p>Sample type</p></td>
<td align="left"><p>Indicates whether the sample is a primary sample or some kind of quality control sample. This field must be populated with one of the acceptable values from the controlled list. Code definitions are provided in <a href="#sample-type-codes">Code definitions</a> below.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="even">
<td align="left"><p>Calibration record</p></td>
<td align="left"><p>Instrument calibrations should be recorded using the appropriate <a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/39004.doc"><em>Form 39004: Instrument calibration log and maintenance schedule</em></a>, according to the <a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/32057.pdf"><em>Instrument calibration log user guide</em> (STOP 32057)</a>. The number to be recorded here is the <em>Instrument book number</em> and <em>Sheet number</em> combined, but separated by a forward slash. For example, if the calibration log for an instrument had an <em>Instrument book number</em> of <em>BA-0123</em>, and a <em>Sheet number</em> of <em>02</em>, then the calibration record to be noted is <em>BA-0123/02</em>. This provides the opportunity to trace back from the collected field data to the original calibration record if required. If more than one calibration record is relevant, note all the relevant record numbers.</p></td>
<td align="left"><p>N</p></td>
</tr>
<tr class="odd">
<td align="left"><p>Instrument</p></td>
<td align="left"><p>The model of water quality instrument used to collect the field measurements. This must be selected from the list of available instruments.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="even">
<td align="left"><p>Sampling Officer</p></td>
<td align="left"><p>Name of the staff member who collected the field measurements.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="odd">
<td align="left"><p>Sample collected</p></td>
<td align="left"><p>Indicates whether a sample has been collected for laboratory analysis, or whether only field measurements have been collected. This is indicated by selecting either <em>Yes</em> or <em>No</em>.</p></td>
<td align="left"><p>N</p></td>
</tr>
<tr class="even">
<td align="left"><p>Depth Upper (m)</p></td>
<td align="left"><p>If a sample is collected at a specific depth, write the depth in metres.</p></td>
<td align="left"><p>Y</p></td>
</tr>
<tr class="odd">
<td align="left"><p>Depth Lower (m)</p></td>
<td align="left"><p>If the sample is collected over a depth range, record the upper depth limit in <em>Depth Upper</em> and lower depth limit in <em>Depth Lower</em>.</p></td>
<td align="left"><p>N</p></td>
</tr>
<tr class="even">
<td align="left"><p>Comments</p></td>
<td align="left"><p>Any relevant text comments that should accompany the data.</p></td>
<td align="left"><p>N</p></td>
</tr>
</tbody>
</table>
<h2 id="field-measurements">Field measurements</h2>
<p>The following columns are available for data collected in the field.</p>
<table border=1>
<thead>
<tr class="header">
<th align="left">Parameter</th>
<th align="center">Unit</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">Dissolved oxygen (DO)</td>
<td align="center">mg/L <em>or</em> % saturation</td>
</tr>
<tr class="even">
<td align="left">pH</td>
<td align="center">pH units</td>
</tr>
<tr class="odd">
<td align="left">Temperature</td>
<td align="center">deg C</td>
</tr>
<tr class="even">
<td align="left">Electrical conductivity (EC)</td>
<td align="center">uS/cm, uncompensated</td>
</tr>
<tr class="odd">
<td align="left">Electrical conductivity (EC) @25C</td>
<td align="center">uS/cm, compensated @25C</td>
</tr>
<tr class="even">
<td align="left">Turbidity</td>
<td align="center">NTU</td>
</tr>
<tr class="odd">
<td align="left">Water depth (water column height)</td>
<td align="center">m</td>
</tr>
<tr class="even">
<td align="left">Gauge height</td>
<td align="center">m</td>
</tr>
</tbody>
</table>
<h2 id="code-definitions">Code definitions</h2>
<h3 id="matrix-codes">Matrix codes<a name="matrix-codes"></a></h3>
<table border=1>
<thead>
<tr class="header">
<th align="left">Code</th>
<th align="left">Definition</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">ST</td>
<td align="left">Stream</td>
</tr>
<tr class="even">
<td align="left">SG</td>
<td align="left">Storage</td>
</tr>
<tr class="odd">
<td align="left">GB</td>
<td align="left">Groundwater bore</td>
</tr>
<tr class="even">
<td align="left">GP</td>
<td align="left">Piezometer</td>
</tr>
<tr class="odd">
<td align="left">PR</td>
<td align="left">Precipitation -- rain</td>
</tr>
<tr class="even">
<td align="left">PS</td>
<td align="left">Precipitation -- snow</td>
</tr>
</tbody>
</table>
<h3 id="sample-type-codes">Sample type codes<a name="sample-type-codes"></a></h3>
<table border=1>
<thead>
<tr class="header">
<th align="left">Code</th>
<th align="left">Definition</th>
</tr>
</thead>
<tbody>
<tr class="odd">
<td align="left">P</td>
<td align="left">Primary</td>
</tr>
<tr class="even">
<td align="left">R</td>
<td align="left">Replicate</td>
</tr>
<tr class="odd">
<td align="left">D</td>
<td align="left">Duplicate</td>
</tr>
<tr class="even">
<td align="left">T</td>
<td align="left">Triplicate</td>
</tr>
<tr class="odd">
<td align="left">QR</td>
<td align="left">Rinsate blank</td>
</tr>
<tr class="even">
<td align="left">QB</td>
<td align="left">Field blank</td>
</tr>
<tr class="odd">
<td align="left">QT</td>
<td align="left">Trip blank</td>
</tr>
</tbody>
</table>
<h1 id="references">References</h1>
<p><a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/32055.pdf"><em>Bulk Data Import into KiWQM Database</em> (STOP 32055)</a></p>
<p><a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/39004.doc"><em>Instrument Calibration Log and Maintenance Schedule</em> (STOP 39004)</a></p>
<p><a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/32057.pdf"><em>Instrument calibration log user guide</em> (STOP 32057)</a></p>
<p><a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/32005.pdf"><em>Water quality project, sample, fraction and station numbers (product identification and traceability)</em> (STOP 32005)</a></p>
<p><a href="http://waterinfo.nsw.gov.au/stop/stop/stop/current-docs/39057.doc"><em>Water Sample Log</em> (STOP 39057)</a></p>
"""