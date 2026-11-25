/* Tooltips: what happens if you press / move this control. Keys are "widget:label" (or "*:label" for any widget). */
window.TIPS = {
  /* ---- header and overlays ---- */
  'chrome:◀': 'Go to the previous slide (keyboard: ←).',
  'chrome:▶': 'Go to the next slide (keyboard: →).',
  'chrome:Slides': 'Open the list of all slides and jump to any of them (keyboard: G).',
  'chrome:Notes': 'Show or hide the instructor notes for this slide: what to say and what to click (keyboard: N).',
  'chrome:Full': 'Show the deck full screen. Press again, or Esc, to leave (keyboard: F).',
  'chrome:?': 'Show the keyboard shortcuts (keyboard: ?).',
  '*:Close': 'Close this panel and go back to the slide.',

  /* ---- dirty log: step through the pipeline ---- */
  'dirtylog:0 raw': 'The log exactly as it arrived: 12 rows, nothing fixed yet.',
  'dirtylog:1 types': 'Strip spaces, turn the decimal comma into a point, convert milliseconds and date text to seconds. No row is removed.',
  'dirtylog:2 incomplete': 'Drop the rows that miss a user, an item, a rating or a time.',
  'dirtylog:3 timestamps': 'Drop the rows whose time is impossible: before the platform existed or after the log was exported.',
  'dirtylog:4 items': 'Drop the rows about items that are not in movies.csv (a merge with indicator=True finds them).',
  'dirtylog:5 repeats': 'Drop rows that are an exact copy of an earlier row.',
  'dirtylog:6 retries': 'Keep only the earliest event of each (user, item) pair.',

  /* ---- order of the steps ---- */
  'order:Start': 'Show the three rows before any step runs.',
  'order:Step 1': 'Run the first operation of each pipeline.',
  'order:Step 2': 'Run the second operation of each pipeline and see what survives.',
};
