# Accessibility review

Included: skip links, accessible form-label associations, live status feedback, keyboard focus indicators, reduced-motion handling, and mobile adaptation.

Manual verification checklist:
- Navigate every page using Tab, Shift+Tab, Enter and Space only.
- Verify focus position and skip-to-content on each page.
- Use NVDA + Firefox and inspect field labels, dynamic messages and tables.
- Test 200% and 400% browser zoom and narrow viewport widths.
- Check text/background contrast with browser accessibility tools.
- Audit all dynamically generated timetable cells and interactive edits.
- Run Lighthouse and axe-core on live pages; preserve issue reports.

These changes do **not** claim WCAG certification.

## Frontend pass — File 4

- Faculty save and timetable actions report outcomes in a non-blocking `role="status"` element instead of an alert dialog.
- Fixed malformed faculty form markup, which prevented the stray "Save Details" fragment from working as intended. The functional Save Faculty Information button remains.
- Accessible labels were added to the editable timetable fields. The editor supports Escape to cancel, and Enter or Space to reopen a saved cell (including after edits). Focus returns to the edited cell.
- Students receive a live feedback message for invalid input. The AI chat toggle exposes its expanded state, supports Escape to close, and restores focus on close.
- Added length limits to selected text inputs and scrollable timetable tables on smaller screens.

### Manual browser checks still required

1. At 200% and 400% zoom, confirm no controls or essential text are obscured.
2. Navigate faculty and student pages using only Tab, Shift+Tab, Enter, Space, and Escape.
3. Use NVDA + Chrome (or another screen reader/browser pair) to verify status announcements, forms, and chat dialog navigation.
4. Run Chrome Lighthouse Accessibility or axe-core to check contrast and labels beyond static tests.
5. Run a complete faculty save/generate/edit/download and student plan/save/load/chat session with the backend running.

Automated static checks do not establish WCAG conformance.
