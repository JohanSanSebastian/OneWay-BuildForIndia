1. UI & Branding Specifications
Typography: Transition the entire interface to a modern minimalist font stack.

Preference: Inter, Geist, or Montserrat (Sans-serif, clean tracking, variable weight).

Remove any default system serifs or "boxy" legacy fonts.

Payment Assets: * The default QR code for all payment modules must now point to the local asset: api-qr.png.

Hardcode this as the primary source; do not fallback to placeholders.

2. Data Integrity & Visualization
Zero-Fabrication Policy: Under no circumstances should the agent generate or display "Sample Data" or "Mock Data" if a query returns empty.

Temporal Constraints: All "Common Graphs" must dynamically scale their X-axis to show only available historical data.

If data starts from Jan 2026, the graph must start at Jan 2026.

Do not pad the timeline with empty leading/trailing months.

3. Architecture & State Management
Backend-Centric Processing: * All data transformation, filtering, and "heavy lifting" must be handled strictly in the backend.

Action: Audit the current frontend codebase and move any logic performing data manipulation or business rules to the backend side. The frontend should remain a "dumb" presentation layer.

Layout Persistence: * Implement state persistence for the user dashboard.

Once a user is logged in, their specific layout configuration must remain immutable across page refreshes.

Ensure the layout state is fetched and locked immediately upon session re-validation.

Implementation Note for Agent:

"Prioritize the backend migration of logic first. Ensure api-qr.png is correctly mapped in the payment gateway component before styling the font to avoid broken assets during the transition."