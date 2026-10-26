P1 — Inspect the repository and plan Phase 1 ELM
Repo: /home/ayush/Documents/Fusion/Fusion-Integrated

You are assisting with Phase 1 of the Employee Leave Management (ELM) feature in the Fusion ERP Django + DRF repository.

First inspect the existing structure, especially modules/placement/, config/settings/base.py, config/urls.py, core/, and the module-authoring documentation. Review the provided ELM use cases and business rules before proposing code.

Identify the smallest Phase 1 implementation that fits the existing project patterns: a Django app, LeaveRequest model, serializer, API views, URL routes, and basic tests under modules/elm/.

Reuse existing authentication, project configuration, and shared utilities. Do not add a new Django project or use FastAPI. Do not edit files yet.

Output a concise list of files to create or change, their responsibilities, assumptions, and any specification gaps that need confirmation.

P2 — Create the initial ELM data model and migration
Repo: /home/ayush/Documents/Fusion/Fusion-Integrated

Implement the minimal Phase 1 ELM data layer inside modules/elm/ using the patterns already followed by the repository.

Create or update models.py with a LeaveRequest model suitable for recording a leave application. Use fields justified by the supplied ELM requirements, including ownership, leave dates, leave type/category, reason, and request status as appropriate. Add useful validation without inventing policy rules absent from the specifications.

Create a Django migration for the model using the repository's conventions. Avoid cross-module foreign keys if the project's architecture prohibits them. Do not change the existing placement module or shared authentication.

Show the exact files changed and explain any assumptions. Do not claim migrations succeeded without command output.

P3 — Add DRF serializer, views, and routes
Repo: /home/ayush/Documents/Fusion/Fusion-Integrated

Using the existing modules/elm/models.py and the conventions in modules/placement/, implement the Phase 1 API layer.

Create or update modules/elm/serializers.py, views.py, and urls.py. Expose only the basic leave-request operations supported by the Phase 1 specification, such as creating a request and viewing the current user's requests. Apply existing authentication and permission patterns, validate incoming fields, and ensure users cannot view or modify requests they do not own.

Use Django REST Framework only. Do not hardcode users, credentials, or example data. Do not invent endpoints unrelated to the Phase 1 scope.

Return the implementation with the list of routes and brief instructions for manually testing each endpoint.

P4 — Register ELM as a Fusion module
Repo: /home/ayush/Documents/Fusion/Fusion-Integrated

Integrate the Phase 1 modules/elm/ app into the existing Fusion ERP base code without disturbing other modules.

Read config/settings/base.py, config/urls.py, and the module registration guidance first. Register modules.elm as a Django domain module and include its API URLs using the same established pattern as modules/placement/.

If the repository requires module registry or permissions metadata for API access, follow its actual conventions and add only the minimum necessary entries. Preserve existing authentication and shared middleware.

Make the smallest possible diff, list changed files, and provide the Django checks that should be run. Do not assert checks pass unless their outputs are available.

P5 — Add basic tests and report remaining Phase 1 gaps
Repo: /home/ayush/Documents/Fusion/Fusion-Integrated

Review the Phase 1 modules/elm/ implementation you just produced. Add basic Django/DRF tests in modules/elm/tests.py that cover at least:
- An authenticated user can submit a valid leave request.
- Invalid request fields are rejected with appropriate validation errors.
- An unauthenticated user is denied access.
- A user cannot access another user's leave requests.

Follow the project's actual fixtures and test conventions. Keep tests limited to functionality implemented in Phase 1; do not claim complete leave approval, balance calculation, or higher-level workflows if they are not present.

Run the available checks and tests when the environment permits. Report passed, failed, and not-run ch