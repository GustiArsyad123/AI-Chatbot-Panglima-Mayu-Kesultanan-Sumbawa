# Metadata schema for ingested documents

Fields (per document chunk)

- **title**: string — title of the source document (from filename or extracted metadata)
- **author**: string — author(s) if known
- **year**: integer — year of publication if known
- **language**: string — language code (e.g., `id` for Indonesian)
- **source_type**: enum — `pdf`, `journal`, `web`, `community`
- **reliability**: enum — `high` (peer-reviewed), `medium` (archival/manual transcription), `low` (community/non-academic)
- **page**: integer — page number in the original document
- **chunk_id**: string — unique id for the chunk (e.g., filename_page_chunkidx)
- **text**: string — the chunk text
- **keywords**: list[string] — extracted or assigned keywords
- **location**: string — physical location of manuscript / archive if known

Usage

- When ingesting a PDF, populate `title` from the filename (or embedded metadata) and `page` per page. Split long pages into `chunks` but preserve original `page` in metadata.
