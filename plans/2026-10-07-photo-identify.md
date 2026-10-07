# Plan: Photo → LLM plant identification (identify-first)

Date: 2026-10-07 · Status: approved for implementation

## Goal

Upload a picture in the Add Plant form → LLM (vision) identifies the plant/tree →
the form's data (name, type, description, cares) gets prefilled for review → user
confirms and saves. The photo is the primary input.

## Background (existing flows being extended)

- `PlantForm.tsx` already accepts an optional photo (saved to media, never sent to LLM).
- On `GardenItem` create, a `post_save` signal queues `generate_item_care_async`
  (django-q) which fills description/cares **from the name only**, then builds the care schedule.
- LLM is `openai` / `gpt-4o` (vision-capable). Providers are an ABC in `apps/llm/providers.py`
  (openai / anthropic / ollama).
- UI pattern for LLM work: async task + polling, ~90s give-up.
- `GardenItemSerializer` is `fields = '__all__'` → description/cares already accepted on create.

## Flow

1. `PlantForm`: photo selected → **"Identify plant"** button appears (Add to garden stays).
2. `POST /api/v1/llm/identify/` (multipart photo) → creates `PlantIdentification`
   (status=pending), queues `identify_plant_async`, returns record id.
3. Task: reads photo, base64, vision prompt → JSON `{name, type, description, cares}`
   → record `complete`, or `failed` + readable error.
4. Form polls `GET /api/v1/llm/identify/<id>/` every 3s (give up ~90s). On success:
   prefill name + type radio, show description/cares for review/edit.
5. Add to garden → existing create, now also sending `description`/`cares`.
   On success, `DELETE /api/v1/llm/identify/<id>/` (removes duplicate photo).
6. Guard: `generate_item_care_async` **skips** description/cares regeneration when both are
   already populated (vision text not clobbered); care schedule still generated.

## Provider change

`generate(prompt, system=None, image_path=None)`:
- `BaseLLMProvider`: `image_path` present and unsupported → raise `VisionNotSupportedError`.
- `OpenAIProvider`: implements (base64 data URL content part).
- `AnthropicProvider` / `OllamaProvider`: raise (clear UI error). No new config/accounts.

## Files

### Backend (`backend/apps/llm/`)
- `models.py` (new) — `PlantIdentification`: photo (ImageField, `upload_to='identify/'`),
  status (pending/complete/failed, default pending), error (Text, blank), name (Char 200, blank),
  type (Char 20, blank, same choices as GardenItem), description/cares (Text, blank),
  created_at/updated_at.
- Migration for the new model.
- `prompts.py` — `PLANT_IDENTIFICATION_PROMPT` (identify from photo; JSON with name, type
  ∈ plant|tree|shrub|other, description 2-3 sentences, cares guide; language instructions
  applied via existing system prompt).
- `providers.py` — image param on `generate`; `VisionNotSupportedError`; OpenAI implements.
- `service.py` — `identify_plant(image_path) -> dict` returning
  `{name, type, description, cares}` or `{error: str}` (logs like existing methods).
- `tasks.py` — `identify_plant_async(identification_id)`; guard in `generate_item_care_async`.
- `views.py` + `urls.py` — POST identify (multipart, requires photo, queues task),
  GET identify status, DELETE identify (removes file).
- `serializers.py` (new) — `PlantIdentificationSerializer`.

### Frontend
- `lib/api.ts` — `llm.identifyUpload(formData)`, `llm.identifyStatus(id)`, `llm.identifyDelete(id)`.
- `lib/hooks.ts` — `useIdentifyPlant` (mutation), `useIdentification(id, active)` poll query
  (3s while pending; timeout ~90s → surfaced as error), `useDeleteIdentification`.
- `components/PlantForm.tsx` — Identify button, prefill via react-hook-form `setValue`,
  suggested description/cares preview, pass them on submit, cleanup delete on success,
  failure/timeout messages.
- `lib/i18n/en.ts` + `lib/i18n/es.ts` — new strings (both languages; i18n parity test covers).

## Tests

### Django (`backend/apps/llm/tests/`, existing layout, LLM never actually called)
- `test_models.py`: PlantIdentification defaults (status=pending, blank fields).
- `test_providers.py`: OpenAI vision payload shape (mocked client: text + image parts,
  base64 data URL); base-class and anthropic/ollama raise `VisionNotSupportedError`.
- `test_service.py`: `identify_plant` — valid JSON, markdown-fenced JSON, malformed → error
  dict, invalid type coerced/flagged.
- `test_tasks.py`: `identify_plant_async` happy path (mocked service) updates record;
  failure path sets status=failed + error; record-missing no-crash.
  **Regression:** `generate_item_care_async` skips description generation when both
  description and cares are already set (still generates schedule); generates when empty.
- `test_views.py`: POST identify queues task + returns id (task mocked), 400 without photo;
  GET returns status/fields; DELETE removes record + file.

### Vitest
- `api.test.ts`: new identify endpoints.
- `i18n.test.ts`: parity (existing test asserts en/es keys match).

## Task order (TDD — test first, then implement)

- [x] 1. Model + migration (+ tests)
- [x] 2. Provider image support + error (+ tests)
- [x] 3. Prompt + service `identify_plant` (+ tests)
- [x] 4. Task `identify_plant_async` (+ tests)
- [x] 5. Care-task skip-if-populated guard (+ regression test)
- [x] 6. Serializer + views + urls (+ tests)
- [x] 7. Frontend api.ts + hooks.ts (+ tests)
- [x] 8. PlantForm UI + i18n strings
- [x] 9. Full verification: `python3 manage.py test`, `npx tsc --noEmit`, `npx vitest run`

## Verification evidence (2026-10-07)

- Backend: `python3 manage.py test` → **110 tests, OK** (baseline was 84; +26 new)
- Frontend: `npx tsc --noEmit` → **TSC OK**
- Frontend: `npx vitest run` → **26 tests passed** (baseline 22; +4 api tests)

## Verification evidence (2026-10-07, final)

- Backend: `python3 manage.py test` → **113 tests, OK** (baseline 84; +29 new)
- Frontend: `npx tsc --noEmit` → **TSC OK**
- Frontend: `npx vitest run` → **26 tests passed** (baseline 22; +4 api tests)

## Code review outcome (subagent, 2026-10-07)

**Ready to merge: With fixes.** No Critical issues. Fixed before commit:

1. **Upload validation** (Important): POST identify now rejects non-`image/*`
   files and caps size at 10 MB (`views.py`); lazy sweep deletes abandoned
   records older than 1h (row + photo file) on each new identify request.
2. **Abandoned-identification cleanup** (Important): server-side lazy sweep
   above + client-side fire-and-forget delete on form unmount.
3. **Photo swap during identification** (Important): file input disabled +
   greyed while identifying; picking a new photo clears the AI draft.
4. **Poll 404 noise** (Minor): `retry: false` on the identification query.
5. **Type list duplication** (Minor): `VALID_ITEM_TYPES` now derived from
   `GardenItem.TYPE_CHOICES` (single source of truth, sync test still passes).

Deferred (noted for later): transient client delete failure (covered by the
server-side sweep); outer try/except in `identify_plant_async` around
bookkeeping (django-q retry makes a double LLM call possible in edge case).

## Notes

- One deviation from the plan, deliberate: the identify record is deleted as soon as the
  result is consumed in the form (on prefill or failure), not only after item creation.
  Safe because the browser still holds the original `File` for the create request; it just
  avoids orphaned records if the user closes the form.

## Verification (evidence before "done")

```bash
cd backend && python3 manage.py test
cd frontend && npx tsc --noEmit
cd frontend && npx vitest run
```

Then manual: add a plant via photo on the deployed site (./deploy.sh) and confirm
identify → prefill → save → care events.

## Out of scope

Re-identifying existing plants' photos, multi-photo, confidence scores,
vision support for anthropic/ollama providers (clear error instead).
